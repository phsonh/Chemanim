#include "Depiction.hpp"
#include "SvgRaster.hpp"

#include <GraphMol/Atom.h>
#include <GraphMol/Bond.h>
#include <GraphMol/Conformer.h>
#include <GraphMol/MolDraw2D/MolDraw2DSVG.h>
#include <GraphMol/MolDraw2D/MolDraw2DUtils.h>
#include <GraphMol/MolOps.h>
#include <GraphMol/RWMol.h>
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/Depictor/RDDepictor.h>

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <memory>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace chem::core {
namespace {
struct BuiltMolecule {
    std::unique_ptr<RDKit::RWMol> value;
    std::vector<std::string> atomIds;
    std::vector<std::string> bondIds;
};

RDKit::Bond::BondType rdBondType(BondType value) {
    switch (value) {
        case BondType::Double: return RDKit::Bond::DOUBLE;
        case BondType::Triple: return RDKit::Bond::TRIPLE;
        case BondType::Aromatic: return RDKit::Bond::AROMATIC;
        default: return RDKit::Bond::SINGLE;
    }
}

BuiltMolecule build(const Molecule& source) {
    BuiltMolecule result; result.value = std::make_unique<RDKit::RWMol>();
    std::unordered_map<std::string, unsigned int> indices;
    const bool stableAromaticDisplay=std::all_of(source.bonds.begin(),source.bonds.end(),[](const Bond& bond){return bond.type!=BondType::Aromatic||bond.displayType.has_value();});
    for (const Atom& value : source.atoms) {
        auto* atom = new RDKit::Atom(value.element.empty() ? "C" : value.element);
        atom->setIsotope(std::max(0, value.isotope)); atom->setFormalCharge(value.formalCharge);
        atom->setNumRadicalElectrons(std::max(0, value.radicalElectrons)); atom->setIsAromatic(value.aromatic&&!stableAromaticDisplay);
        if (value.implicitHydrogens > 0) { atom->setNoImplicit(true); atom->setNumExplicitHs(value.implicitHydrogens); }
        const unsigned int index = result.value->addAtom(atom, true, true);
        if (value.hidden) result.value->getAtomWithIdx(index)->setProp(RDKit::common_properties::atomLabel, std::string{});
        else if (!value.alias.empty()) result.value->getAtomWithIdx(index)->setProp(RDKit::common_properties::atomLabel, value.alias);
        indices[value.id] = index; result.atomIds.push_back(value.id);
    }
    for (const Bond& value : source.bonds) {
        if(!value.visible)continue;
        const auto a = indices.find(value.atomA), b = indices.find(value.atomB);
        if (a == indices.end() || b == indices.end() || a->second == b->second) continue;
        const BondType depictedType=value.type==BondType::Aromatic&&value.displayType?*value.displayType:value.type;
        result.value->addBond(a->second, b->second, rdBondType(depictedType));
        RDKit::Bond* bond = result.value->getBondBetweenAtoms(a->second, b->second);
        if (value.type == BondType::Aromatic&&!value.displayType) { bond->setIsAromatic(true); result.value->getAtomWithIdx(a->second)->setIsAromatic(true); result.value->getAtomWithIdx(b->second)->setIsAromatic(true); }
        if (value.stereo == BondStereo::SolidWedge) bond->setBondDir(RDKit::Bond::BEGINWEDGE);
        else if (value.stereo == BondStereo::DashedWedge) bond->setBondDir(RDKit::Bond::BEGINDASH);
        else if (value.stereo == BondStereo::Wavy) bond->setBondDir(RDKit::Bond::UNKNOWN);
        result.bondIds.push_back(value.id);
    }
    auto* conformer = new RDKit::Conformer(static_cast<unsigned int>(source.atoms.size())); conformer->set3D(false);
    for (unsigned int index = 0; index < source.atoms.size(); ++index) {
        const Point point = source.atoms[index].position;
        conformer->setAtomPos(index, RDGeom::Point3D(point.x, point.y, 0.0));
    }
    result.value->addConformer(conformer, true);
    try { RDKit::MolOps::sanitizeMol(*result.value); } catch (...) { result.value->updatePropertyCache(false); }
    // Preparation is deliberately performed on this transient copy. Kekulization
    // and drawing cleanup must never mutate the authoritative atom/bond/XY table.
    try {
        RDKit::MolDraw2DUtils::prepareMolForDrawing(*result.value,
            /*kekulize=*/true, /*addChiralHs=*/false, /*wedgeBonds=*/false,
            /*forceCoords=*/false, /*wavyBonds=*/true);
    } catch (...) {
        result.value->updatePropertyCache(false);
    }
    return result;
}

std::vector<Point> bondHitPolygon(Point first, Point second, double padding) {
    Point tangent{second.x - first.x, second.y - first.y};
    const double length = std::max(1e-9, std::hypot(tangent.x, tangent.y)); tangent.x /= length; tangent.y /= length;
    const Point normal{-tangent.y * padding, tangent.x * padding};
    const Point extension{tangent.x * padding, tangent.y * padding};
    return {{first.x - extension.x + normal.x, first.y - extension.y + normal.y},
            {second.x + extension.x + normal.x, second.y + extension.y + normal.y},
            {second.x + extension.x - normal.x, second.y + extension.y - normal.y},
            {first.x - extension.x - normal.x, first.y - extension.y - normal.y}};
}
}  // namespace

DepictionResult DepictionCore::depict(const Molecule& molecule, const Style& style, const Viewport& viewport) const {
    DepictionResult result; result.width = viewport.width; result.height = viewport.height;
    if (molecule.atoms.empty()) {
        result.svg = "<svg xmlns='http://www.w3.org/2000/svg' width='" + std::to_string(viewport.width) + "px' height='" + std::to_string(viewport.height) + "px'></svg>";
        return result;
    }
    BuiltMolecule built = build(molecule);
    double minX=molecule.atoms.front().position.x,maxX=minX,minY=molecule.atoms.front().position.y,maxY=minY;
    for(const Atom& atom:molecule.atoms){minX=std::min(minX,atom.position.x);maxX=std::max(maxX,atom.position.x);minY=std::min(minY,atom.position.y);maxY=std::max(maxY,atom.position.y);}
    const double referenceBondLength = molecule.referenceBondLength > 0 ? molecule.referenceBondLength : 1.0;
    const double acsModelScale = 14.4 / referenceBondLength;
    const int virtualWidth=std::max(4096,static_cast<int>(std::ceil((maxX-minX)*acsModelScale+2048.0)));
    const int virtualHeight=std::max(4096,static_cast<int>(std::ceil((maxY-minY)*acsModelScale+2048.0)));
    RDKit::MolDraw2DSVG drawer(virtualWidth, virtualHeight);
    auto& options = drawer.drawOptions();
    options.clearBackground = false; options.prepareMolsBeforeDrawing = false;
    if (!style.fontFile.empty()) options.fontFile = style.fontFile;
    RDKit::MolDraw2DUtils::setACS1996Options(options, referenceBondLength);
    drawer.drawMolecule(*built.value);
    const auto origin = drawer.getDrawCoords(RDGeom::Point2D(0.0, 0.0));
    const auto unit = drawer.getDrawCoords(RDGeom::Point2D(1.0, 0.0));
    const double canonicalModelScale = std::hypot(unit.x - origin.x, unit.y - origin.y);
    const double uniformScale = viewport.pixelsPerUnit / canonicalModelScale;
    const double viewWidth = viewport.width / uniformScale;
    const double viewHeight = viewport.height / uniformScale;
    const double viewLeft=origin.x+canonicalModelScale*viewport.center.x-viewWidth*.5;
    const double viewTop=origin.y-canonicalModelScale*viewport.center.y-viewHeight*.5;
    result.modelScale = canonicalModelScale * uniformScale;
    result.modelOrigin = {viewport.width * .5 - viewport.center.x * viewport.pixelsPerUnit,
                          viewport.height * .5 + viewport.center.y * viewport.pixelsPerUnit};
    result.atoms.reserve(molecule.atoms.size());
    for (unsigned int index = 0; index < molecule.atoms.size(); ++index) {
        const auto rawPoint = drawer.getDrawCoords(index); const Point point{(rawPoint.x-viewLeft)*uniformScale,(rawPoint.y-viewTop)*uniformScale}; const Atom& atom = molecule.atoms[index];
        const double width = (atom.element == "C" && atom.alias.empty() ? 10.0 : std::max(18.0, 8.0 * static_cast<double>((atom.alias.empty() ? atom.element : atom.alias).size()))) * uniformScale;
        const double halfHeight = 9.0 * uniformScale;
        result.atoms.push_back({atom.id, point, {point.x - width * .5, point.y - halfHeight, point.x + width * .5, point.y + halfHeight}});
    }
    result.bonds.reserve(molecule.bonds.size());
    for (std::size_t index = 0; index < molecule.bonds.size(); ++index) {
        const Bond& bond = molecule.bonds[index];
        if(!bond.visible)continue;
        const auto a = std::find_if(result.atoms.begin(), result.atoms.end(), [&](const AtomGeometry& value) { return value.id == bond.atomA; });
        const auto b = std::find_if(result.atoms.begin(), result.atoms.end(), [&](const AtomGeometry& value) { return value.id == bond.atomB; });
        if (a != result.atoms.end() && b != result.atoms.end()) result.bonds.push_back({bond.id, a->center, b->center, bondHitPolygon(a->center, b->center, 7.0)});
    }
    drawer.finishDrawing(); result.svg = drawer.getDrawingText();
    result.svg=std::regex_replace(result.svg,std::regex("width='[0-9.]+px'"),"width='"+std::to_string(viewport.width)+"px'",std::regex_constants::format_first_only);
    result.svg=std::regex_replace(result.svg,std::regex("height='[0-9.]+px'"),"height='"+std::to_string(viewport.height)+"px'",std::regex_constants::format_first_only);
    std::ostringstream viewBox; viewBox<<std::setprecision(12)<<"viewBox='"<<viewLeft<<' '<<viewTop<<' '<<viewWidth<<' '<<viewHeight<<"'";
    result.svg=std::regex_replace(result.svg,std::regex("viewBox='[^']+'"),viewBox.str(),std::regex_constants::format_first_only);
    return result;
}

RasterResult DepictionCore::rasterize(const DepictionResult& depiction, double scale) const { return rasterizeSvg(depiction.svg, scale); }

Molecule moleculeFromSmiles(const std::string& stableId, const std::string& name, const std::string& smiles) {
    std::unique_ptr<RDKit::ROMol> parsed(RDKit::SmilesToMol(smiles));
    if (!parsed) throw std::runtime_error("RDKit could not parse the SMILES string");
    RDDepict::compute2DCoords(*parsed, nullptr, true, true);
    const RDKit::Conformer& conformer = parsed->getConformer();
    RDKit::RWMol preparedForStereo(*parsed);
    try {
        RDKit::MolDraw2DUtils::prepareMolForDrawing(preparedForStereo,
            /*kekulize=*/true, /*addChiralHs=*/false, /*wedgeBonds=*/true,
            /*forceCoords=*/false, /*wavyBonds=*/true);
    } catch (...) {
        preparedForStereo.updatePropertyCache(false);
    }
    Molecule result; result.id = stableId; result.name = name.empty() ? stableId : name; result.sourceSmiles = smiles;
    std::vector<std::string> ids(parsed->getNumAtoms());
    for (unsigned int index = 0; index < parsed->getNumAtoms(); ++index) {
        const RDKit::Atom* source = parsed->getAtomWithIdx(index); const auto point = conformer.getAtomPos(index);
        std::uint64_t number = source->getAtomMapNum() ? source->getAtomMapNum() : result.nextAtomId++;
        std::string id = "A" + std::to_string(number); while (result.atom(id)) id = "A" + std::to_string(result.nextAtomId++);
        result.nextAtomId = std::max(result.nextAtomId, number + 1); ids[index] = id;
        result.atoms.push_back(Atom{.id=id, .element=source->getSymbol(), .isotope=static_cast<int>(source->getIsotope()),
            .formalCharge=source->getFormalCharge(), .radicalElectrons=static_cast<int>(source->getNumRadicalElectrons()),
            .implicitHydrogens=static_cast<int>(source->getTotalNumHs(false)), .aromatic=source->getIsAromatic(), .position={point.x,point.y}});
    }
    for (const RDKit::Bond* source : parsed->bonds()) {
        BondType type = source->getIsAromatic() ? BondType::Aromatic : source->getBondType() == RDKit::Bond::DOUBLE ? BondType::Double : source->getBondType() == RDKit::Bond::TRIPLE ? BondType::Triple : BondType::Single;
        const RDKit::Bond* depictedBond = preparedForStereo.getBondWithIdx(source->getIdx());
        BondStereo stereo = depictedBond->getBondDir() == RDKit::Bond::BEGINWEDGE ? BondStereo::SolidWedge : depictedBond->getBondDir() == RDKit::Bond::BEGINDASH ? BondStereo::DashedWedge : depictedBond->getBondDir() == RDKit::Bond::UNKNOWN ? BondStereo::Wavy : BondStereo::None;
        std::optional<BondType> displayType;
        if(type==BondType::Aromatic){
            const RDKit::Bond* kekuleBond=preparedForStereo.getBondWithIdx(source->getIdx());
            displayType=kekuleBond->getBondType()==RDKit::Bond::DOUBLE?BondType::Double:BondType::Single;
        }
        result.bonds.push_back({"B" + std::to_string(result.nextBondId++), ids[source->getBeginAtomIdx()], ids[source->getEndAtomIdx()], type, displayType, stereo, true});
    }
    result.referenceBondLength = RDKit::MolDraw2DUtils::meanBondLength(*parsed);
    return result;
}

}  // namespace chem::core
