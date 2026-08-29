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
#include <cctype>
#include <cmath>
#include <iomanip>
#include <memory>
#include <numbers>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace chem::core {
namespace {
double pointDistance(Point first,Point second){return std::hypot(first.x-second.x,first.y-second.y);}
struct BuiltMolecule {
    std::unique_ptr<RDKit::RWMol> value;
    std::vector<std::string> atomIds;
    std::vector<std::string> bondIds;
    std::unordered_map<std::string, unsigned int> indices;
    std::vector<Point> positions;
};

std::vector<std::string> labelGroups(const std::string& source) {
    std::vector<std::string> groups;
    for (std::size_t index = 0; index < source.size();) {
        const unsigned char current = static_cast<unsigned char>(source[index]);
        if (std::isupper(current)) {
            std::size_t end = index + 1;
            if (end < source.size() && std::islower(static_cast<unsigned char>(source[end]))) ++end;
            while (end < source.size() && std::isdigit(static_cast<unsigned char>(source[end]))) ++end;
            groups.push_back(source.substr(index, end - index)); index = end;
        } else {
            std::size_t end = index + 1;
            while (end < source.size() && std::isdigit(current) ==
                    std::isdigit(static_cast<unsigned char>(source[end]))) ++end;
            groups.push_back(source.substr(index, end - index)); index = end;
        }
    }
    return groups;
}

std::string orientedAlias(const Atom& atom) {
    if (atom.alias.empty()) return {};
    std::vector<std::string> groups = labelGroups(atom.alias);
    if (atom.labelSide == AtomLabelSide::Left) std::reverse(groups.begin(), groups.end());
    std::string oriented;
    for (const std::string& group : groups) oriented += group;
    return oriented;
}

std::string formattedAlias(const Atom& atom) {
    const std::string oriented = orientedAlias(atom);
    const char* tag = atom.numberStyle == AtomNumberStyle::Subscript ? "sub" : "sup";
    std::string result;
    for (std::size_t index = 0; index < oriented.size();) {
        if (!std::isdigit(static_cast<unsigned char>(oriented[index]))) {
            result.push_back(oriented[index++]); continue;
        }
        std::size_t end = index + 1;
        while (end < oriented.size() && std::isdigit(static_cast<unsigned char>(oriented[end]))) ++end;
        result += "<" + std::string(tag) + ">" + oriented.substr(index, end - index) +
                  "</" + std::string(tag) + ">";
        index = end;
    }
    return result;
}

RDKit::Bond::BondType rdBondType(BondType value) {
    switch (value) {
        case BondType::Double: return RDKit::Bond::DOUBLE;
        case BondType::Triple: return RDKit::Bond::TRIPLE;
        default: return RDKit::Bond::SINGLE;
    }
}

BuiltMolecule build(const Molecule& source) {
    BuiltMolecule result; result.value = std::make_unique<RDKit::RWMol>();
    for (const Atom& value : source.atoms) {
        if (!value.alive) continue;
        auto* atom = new RDKit::Atom(value.element.empty() ? "C" : value.element);
        atom->setIsotope(std::max(0, value.isotope)); atom->setFormalCharge(0);
        atom->setNumRadicalElectrons(std::max(0, value.radicalElectrons));
        if (value.implicitHydrogens > 0) { atom->setNoImplicit(true); atom->setNumExplicitHs(value.implicitHydrogens); }
        const unsigned int index = result.value->addAtom(atom, true, true);
        if (value.hidden) result.value->getAtomWithIdx(index)->setProp(RDKit::common_properties::atomLabel, std::string{});
        else if (!value.alias.empty()) {
            // The atom-label parser intentionally treats digits as
            // subscripts. Normal-number labels are drawn after the molecule
            // through the literal drawString overload instead of passing
            // <lit> through atomLabel (where this RDKit build displays the
            // tag itself).
            if (value.numberStyle == AtomNumberStyle::Normal)
                result.value->getAtomWithIdx(index)->setProp(
                    RDKit::common_properties::atomLabel, std::string{});
            else
                result.value->getAtomWithIdx(index)->setProp(
                    RDKit::common_properties::atomLabel, formattedAlias(value));
        }
        result.indices[value.id] = index; result.atomIds.push_back(value.id);result.positions.push_back(value.position);
    }
    for (const Bond& value : source.bonds) {
        if(!value.visible || !value.alive)continue;
        const auto a = result.indices.find(value.atomA), b = result.indices.find(value.atomB);
        if (a == result.indices.end() || b == result.indices.end() || a->second == b->second) continue;
        result.value->addBond(a->second, b->second, rdBondType(value.type));
        RDKit::Bond* bond = result.value->getBondBetweenAtoms(a->second, b->second);
        if (value.stereo == BondStereo::SolidWedge) bond->setBondDir(RDKit::Bond::BEGINWEDGE);
        else if (value.stereo == BondStereo::DashedWedge) bond->setBondDir(RDKit::Bond::BEGINDASH);
        else if (value.stereo == BondStereo::Wavy) bond->setBondDir(RDKit::Bond::UNKNOWN);
        result.bondIds.push_back(value.id);
    }
    auto* conformer = new RDKit::Conformer(static_cast<unsigned int>(result.positions.size())); conformer->set3D(false);
    for (unsigned int index = 0; index < result.positions.size(); ++index) {
        const Point point = result.positions[index];
        conformer->setAtomPos(index, RDGeom::Point3D(point.x, point.y, 0.0));
    }
    result.value->addConformer(conformer, true);
    result.value->updatePropertyCache(false);
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

std::string rgb(const Color& local, const Color& molecule) {
    const int r = std::clamp(local.red * molecule.red / 255, 0, 255);
    const int g = std::clamp(local.green * molecule.green / 255, 0, 255);
    const int b = std::clamp(local.blue * molecule.blue / 255, 0, 255);
    std::ostringstream stream; stream << "rgb(" << r << ',' << g << ',' << b << ')'; return stream.str();
}
std::string hexColor(const Color& local,const Color& molecule){const int r=std::clamp(local.red*molecule.red/255,0,255),g=std::clamp(local.green*molecule.green/255,0,255),b=std::clamp(local.blue*molecule.blue/255,0,255);std::ostringstream stream;stream<<'#'<<std::uppercase<<std::hex<<std::setfill('0')<<std::setw(2)<<r<<std::setw(2)<<g<<std::setw(2)<<b;return stream.str();}

template <typename Drawer>
std::string adornmentSvg(const Molecule& molecule, const Style& style, Drawer& drawer) {
    std::ostringstream svg; svg << std::setprecision(12);
    const double radius=style.fontPt*.38;
    const double stroke=std::max(style.lineWidthPt,style.fontPt*.065);
    const double arm=radius*.48;
    for(const AtomAdornment& adornment:molecule.adornments){
        const Atom* owner=molecule.atom(adornment.atomId);
        if(!adornment.alive||!owner||!owner->alive)continue;
        const auto center=drawer.getDrawCoords(RDGeom::Point2D(
            owner->position.x+adornment.offset.x,owner->position.y+adornment.offset.y));
        const std::string color=rgb(adornment.color,molecule.color);
        const double opacity=std::clamp(adornment.alpha*molecule.alpha/(255.0*255.0),0.0,1.0);
        const bool negative=adornment.text.find("⊖")!=std::string::npos||
                            adornment.text.find("−")!=std::string::npos||
                            adornment.text.find('-')!=std::string::npos;
        svg<<"<g class='formal-charge' fill='none' stroke='"<<color
           <<"' stroke-width='"<<stroke<<"' stroke-linecap='round' opacity='"<<opacity<<"'>\n"
           <<"<circle cx='"<<center.x<<"' cy='"<<center.y<<"' r='"<<radius<<"'/>\n"
           <<"<path d='M "<<center.x-arm<<','<<center.y<<" L "<<center.x+arm<<','<<center.y<<"'/>\n";
        if(!negative)svg<<"<path d='M "<<center.x<<','<<center.y-arm<<" L "<<center.x<<','<<center.y+arm<<"'/>\n";
        svg<<"</g>\n";
    }
    return svg.str();
}

void appendLine(std::ostringstream& svg, RDGeom::Point2D first, RDGeom::Point2D second,
                double width, const std::string& color, double opacity,
                const char* lineCap = "round") {
    svg << "<path d='M " << first.x << ',' << first.y << " L " << second.x << ',' << second.y
        << "' fill='none' stroke='" << color << "' stroke-width='" << width
        << "' stroke-linecap='" << lineCap << "' stroke-linejoin='round' opacity='" << opacity << "'/>\n";
}

template <typename Drawer>
std::string explicitBondSvg(const Molecule& molecule, const Style& style, Drawer& drawer) {
    std::ostringstream svg; svg << std::setprecision(12);
    const double reference = std::max(.01, molecule.referenceBondLength);
    const double modelSpacing = style.bondLengthPt * style.doubleBondSpacing / (style.bondLengthPt / reference);
    const double halfCentered = modelSpacing * .5;
    const double modelPerPoint=reference/std::max(.01,style.bondLengthPt);
    const auto labelExtents=[&](const Atom* atom)->Point{
        if(!atom||atom->hidden||(atom->element=="C"&&atom->alias.empty()))return {};
        std::size_t glyphs=(atom->alias.empty()?atom->element:atom->alias).size();
        if(atom->implicitHydrogens>0)glyphs+=1+(atom->implicitHydrogens>1?1:0);
        return {(std::max(style.fontPt*.38,style.fontPt*.28*glyphs)+style.lineWidthPt)*modelPerPoint,
                (style.fontPt*.50+style.lineWidthPt)*modelPerPoint};
    };
    const auto clipped=[&](const Atom* atom,Point toward,Point offset,double minimum=0.0){
        const double vx=toward.x-atom->position.x,vy=toward.y-atom->position.y;
        const double magnitude=std::max(1e-9,std::hypot(vx,vy));const Point direction{vx/magnitude,vy/magnitude};
        double amount=minimum;const Point extents=labelExtents(atom);
        if(extents.x>0.0&&extents.y>0.0){
            const double hx=extents.x,hy=extents.y;
            const double qa=direction.x*direction.x/(hx*hx)+direction.y*direction.y/(hy*hy);
            const double qb=2.0*(offset.x*direction.x/(hx*hx)+offset.y*direction.y/(hy*hy));
            const double qc=offset.x*offset.x/(hx*hx)+offset.y*offset.y/(hy*hy)-1.0;
            const double discriminant=std::max(0.0,qb*qb-4.0*qa*qc);
            amount=std::max(amount,(-qb+std::sqrt(discriminant))/(2.0*qa));
        }
        return Point{atom->position.x+offset.x+direction.x*amount,
                     atom->position.y+offset.y+direction.y*amount};
    };
    for (const Bond& bond : molecule.bonds) {
        const Atom* a=molecule.atom(bond.atomA); const Atom* b=molecule.atom(bond.atomB);
        if (!bond.alive || !bond.visible || !a || !b || !a->alive || !b->alive) continue;
        const double dx=b->position.x-a->position.x, dy=b->position.y-a->position.y;
        const double length=std::max(1e-9,std::hypot(dx,dy)); const Point normal{-dy/length,dx/length};
        const Point tangent{dx/length,dy/length};
        const auto point=[&](Point p){return drawer.getDrawCoords(RDGeom::Point2D(p.x,p.y));};
        const std::string color=rgb(bond.color,molecule.color);
        const double opacity=std::clamp(bond.alpha*molecule.alpha/(255.0*255.0),0.0,1.0);
        const double lineWidth=style.lineWidthPt;
        const auto line=[&](Point offset,double minimum=0.0,const char* lineCap="round"){
            appendLine(svg,point(clipped(a,b->position,offset,minimum)),
                       point(clipped(b,a->position,offset,minimum)),lineWidth,color,opacity,lineCap);
        };
        if (bond.stereo==BondStereo::SolidWedge) {
            const Point n{normal.x*modelSpacing,normal.y*modelSpacing};
            const auto p0=point(clipped(a,b->position,{})),p1=point(clipped(b,a->position,n)),p2=point(clipped(b,a->position,{-n.x,-n.y}));
            svg<<"<path d='M "<<p0.x<<','<<p0.y<<" L "<<p1.x<<','<<p1.y<<" L "<<p2.x<<','<<p2.y<<" Z' fill='"<<color<<"' opacity='"<<opacity<<"'/>\n";
            continue;
        }
        if (bond.stereo==BondStereo::DashedWedge) {
            const double t0=pointDistance(a->position,clipped(a,b->position,{}))/length,t1=1.0-pointDistance(b->position,clipped(b,a->position,{}))/length;
            // ACS-style hashed wedges use a few substantial bars. Seven thin
            // round-ended strokes read as a comb and differ visibly from the
            // ChemDraw 1996 document style.
            constexpr int hashCount=5;
            for(int i=1;i<=hashCount;++i){const double t=t0+(t1-t0)*i/(hashCount+1.0);const double w=modelSpacing*t;Point c{a->position.x+dx*t,a->position.y+dy*t};appendLine(svg,point({c.x-normal.x*w,c.y-normal.y*w}),point({c.x+normal.x*w,c.y+normal.y*w}),lineWidth*1.18,color,opacity,"butt");} continue;
        }
        if (bond.stereo==BondStereo::SolidBar) {
            // Keep the constant-width bond visibly heavier than a normal bond
            // without overwhelming the atom junction: ChemDraw's document
            // symbol is about four normal pen widths in total.
            const double halfWidth=lineWidth*modelPerPoint*2.0;
            const Point n{normal.x*halfWidth,normal.y*halfWidth};
            const auto joinsOtherBond=[&](const Atom* atom){
                if(!atom||labelExtents(atom).x>0.0)return false;
                return std::any_of(molecule.bonds.begin(),molecule.bonds.end(),
                    [&](const Bond& candidate){
                        if(candidate.id==bond.id||!candidate.alive||!candidate.visible)return false;
                        if(candidate.atomA!=atom->id&&candidate.atomB!=atom->id)return false;
                        const Atom* other=molecule.atom(
                            candidate.atomA==atom->id?candidate.atomB:candidate.atomA);
                        return other&&other->alive;
                    });
            };
            const bool fillStart=joinsOtherBond(a),fillEnd=joinsOtherBond(b);
            const double shoulder=std::min(halfWidth,length*.25);
            const Point startTip=clipped(a,b->position,{});
            const Point endTip=clipped(b,a->position,{});
            const Point startUpper=fillStart
                ? Point{startTip.x+tangent.x*shoulder+n.x,
                        startTip.y+tangent.y*shoulder+n.y}
                : clipped(a,b->position,n);
            const Point startLower=fillStart
                ? Point{startTip.x+tangent.x*shoulder-n.x,
                        startTip.y+tangent.y*shoulder-n.y}
                : clipped(a,b->position,{-n.x,-n.y});
            const Point endUpper=fillEnd
                ? Point{endTip.x-tangent.x*shoulder+n.x,
                        endTip.y-tangent.y*shoulder+n.y}
                : clipped(b,a->position,n);
            const Point endLower=fillEnd
                ? Point{endTip.x-tangent.x*shoulder-n.x,
                        endTip.y-tangent.y*shoulder-n.y}
                : clipped(b,a->position,{-n.x,-n.y});
            const auto startUpperDraw=point(startUpper),endUpperDraw=point(endUpper);
            const auto endLowerDraw=point(endLower),startLowerDraw=point(startLower);
            svg<<"<path class='solid-bar bond-"<<bond.id<<"' d='";
            if(fillStart){const auto tip=point(startTip);svg<<"M "<<tip.x<<','<<tip.y<<" L ";}
            else svg<<"M ";
            svg<<startUpperDraw.x<<','<<startUpperDraw.y<<" L "
               <<endUpperDraw.x<<','<<endUpperDraw.y;
            if(fillEnd){const auto tip=point(endTip);svg<<" L "<<tip.x<<','<<tip.y;}
            svg<<" L "<<endLowerDraw.x<<','<<endLowerDraw.y<<" L "
               <<startLowerDraw.x<<','<<startLowerDraw.y
               <<" Z' fill='"<<color<<"' opacity='"<<opacity<<"'/>\n";
            continue;
        }
        if (bond.stereo==BondStereo::HashedBar) {
            const double halfWidth=lineWidth*modelPerPoint*2.0;
            const Point first=clipped(a,b->position,{}),second=clipped(b,a->position,{});
            // ChemDraw leaves a half-step margin at both atom endpoints.  Bars
            // at t=0/1 form the conspicuous black caps seen at ring junctions.
            constexpr int hashCount=6;
            for(int i=1;i<=hashCount;++i){
                const double t=i/static_cast<double>(hashCount+1);
                const Point c{first.x+(second.x-first.x)*t,first.y+(second.y-first.y)*t};
                appendLine(svg,point({c.x-normal.x*halfWidth,c.y-normal.y*halfWidth}),
                           point({c.x+normal.x*halfWidth,c.y+normal.y*halfWidth}),
                           lineWidth,color,opacity,"butt");
            }
            continue;
        }
        if (bond.stereo==BondStereo::Wavy) {
            const double t0=pointDistance(a->position,clipped(a,b->position,{}))/length,t1=1.0-pointDistance(b->position,clipped(b,a->position,{}))/length;
            // Sample densely enough that NanoSVG produces a smooth wave rather
            // than the old angular lightning-bolt polyline.
            constexpr int samples=64;
            svg<<"<path d='";for(int i=0;i<=samples;++i){const double t=t0+(t1-t0)*i/samples;const double w=std::sin(i/static_cast<double>(samples)*8.0*std::numbers::pi)*modelSpacing*.25;const auto p=point({a->position.x+dx*t+normal.x*w,a->position.y+dy*t+normal.y*w});svg<<(i?" L ":"M ")<<p.x<<','<<p.y;}svg<<"' fill='none' stroke='"<<color<<"' stroke-width='"<<lineWidth<<"' stroke-linecap='round' stroke-linejoin='round' opacity='"<<opacity<<"'/>\n";continue;
        }
        if (bond.type==BondType::Single) {line({});continue;}
        if (bond.type==BondType::Triple) {
            line({});for(double sign:{-1.0,1.0})line({normal.x*modelSpacing*sign,normal.y*modelSpacing*sign},0.0,"butt");
            continue;
        }
        if (bond.secondaryLineSide==SecondaryLineSide::Center) {
            const auto endpointExtension=[&](const Atom* atom,bool first,double sign){
                if(!atom||labelExtents(atom).x>0.0)return 0.0;
                double best=0.0;
                for(const Bond& candidate:molecule.bonds){
                    if(candidate.id==bond.id||!candidate.alive||!candidate.visible||
                       (candidate.atomA!=atom->id&&candidate.atomB!=atom->id))continue;
                    const Atom* neighbour=molecule.atom(candidate.atomA==atom->id?candidate.atomB:candidate.atomA);
                    if(!neighbour||!neighbour->alive)continue;
                    const double ux=neighbour->position.x-atom->position.x;
                    const double uy=neighbour->position.y-atom->position.y;
                    const double magnitude=std::hypot(ux,uy);
                    if(magnitude<1e-9)continue;
                    const double un=(ux*normal.x+uy*normal.y)/magnitude;
                    const double ut=(ux*tangent.x+uy*tangent.y)/magnitude;
                    if(std::abs(un)<1e-6)continue;
                    // ChemDraw's user-centred double uses a flat end at the
                    // atom projection for one stroke. Only the stroke facing a
                    // neighbouring bond is extended to their intersection.
                    const double ray=sign*halfCentered/un;
                    if(ray<=0.0||ray>length*.35)continue;
                    const double extension=ray*ut;
                    if((first&&extension>=-1e-6)||(!first&&extension<=1e-6))continue;
                    if(best==0.0||std::abs(extension)<std::abs(best))best=extension;
                }
                return std::clamp(best,-length*.25,length*.25);
            };
            for(double sign:{-1.0,1.0}){
                const double extensionA=endpointExtension(a,true,sign);
                const double extensionB=endpointExtension(b,false,sign);
                const Point offset{normal.x*halfCentered*sign,normal.y*halfCentered*sign};
                const Point first=labelExtents(a).x>0.0?clipped(a,b->position,offset):
                    Point{a->position.x+offset.x+tangent.x*extensionA,
                          a->position.y+offset.y+tangent.y*extensionA};
                const Point second=labelExtents(b).x>0.0?clipped(b,a->position,offset):
                    Point{b->position.x+offset.x+tangent.x*extensionB,
                          b->position.y+offset.y+tangent.y*extensionB};
                appendLine(svg,point(first),point(second),lineWidth,color,opacity,"butt");
            }
        } else {
            line({});
            const double sign=bond.secondaryLineSide==SecondaryLineSide::Left?1.0:-1.0;
            // A flat cap avoids the isolated black bead visible where a
            // shortened alkene/ring secondary line approaches a single bond.
            line({normal.x*modelSpacing*sign,normal.y*modelSpacing*sign},length*.16,"butt");
        }
    }
    return svg.str();
}
}  // namespace

DepictionResult DepictionCore::depict(const Molecule& molecule, const Style& style, const Viewport& viewport) const {
    DepictionResult result; result.width = viewport.width; result.height = viewport.height;
    if (std::none_of(molecule.atoms.begin(),molecule.atoms.end(),[](const Atom& atom){return atom.alive;})) {
        result.svg = "<svg xmlns='http://www.w3.org/2000/svg' width='" + std::to_string(viewport.width) + "px' height='" + std::to_string(viewport.height) + "px'></svg>";
        result.viewBox = {0.0, 0.0, static_cast<double>(viewport.width), static_cast<double>(viewport.height)};
        return result;
    }
    BuiltMolecule built = build(molecule);
    const Atom& firstAlive=*std::find_if(molecule.atoms.begin(),molecule.atoms.end(),[](const Atom& atom){return atom.alive;});
    double minX=firstAlive.position.x,maxX=minX,minY=firstAlive.position.y,maxY=minY;
    for(const Atom& atom:molecule.atoms){if(!atom.alive)continue;minX=std::min(minX,atom.position.x);maxX=std::max(maxX,atom.position.x);minY=std::min(minY,atom.position.y);maxY=std::max(maxY,atom.position.y);}
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
    for (const Atom& atom : molecule.atoms) {
        if (!atom.alive || atom.hidden || atom.alias.empty() ||
            atom.numberStyle != AtomNumberStyle::Normal) continue;
        drawer.setColour(RDKit::DrawColour(
            std::clamp(atom.color.red * molecule.color.red / (255.0 * 255.0), 0.0, 1.0),
            std::clamp(atom.color.green * molecule.color.green / (255.0 * 255.0), 0.0, 1.0),
            std::clamp(atom.color.blue * molecule.color.blue / (255.0 * 255.0), 0.0, 1.0),
            std::clamp(atom.alpha * molecule.alpha / (255.0 * 255.0), 0.0, 1.0)));
        drawer.drawString(orientedAlias(atom),
            RDGeom::Point2D(atom.position.x, atom.position.y),
            atom.labelSide == AtomLabelSide::Left
                ? RDKit::MolDraw2D_detail::TextAlignType::END
                : RDKit::MolDraw2D_detail::TextAlignType::START);
    }
    const auto origin = drawer.getDrawCoords(RDGeom::Point2D(0.0, 0.0));
    const auto unit = drawer.getDrawCoords(RDGeom::Point2D(1.0, 0.0));
    const double canonicalModelScale = std::hypot(unit.x - origin.x, unit.y - origin.y);
    const double uniformScale = viewport.pixelsPerUnit / canonicalModelScale;
    const double viewWidth = viewport.width / uniformScale;
    const double viewHeight = viewport.height / uniformScale;
    const double viewLeft=origin.x+canonicalModelScale*viewport.center.x-viewWidth*.5;
    const double viewTop=origin.y-canonicalModelScale*viewport.center.y-viewHeight*.5;
    result.viewBox = {viewLeft, viewTop, viewLeft + viewWidth, viewTop + viewHeight};
    result.modelScale = canonicalModelScale * uniformScale;
    result.modelOrigin = {viewport.width * .5 - viewport.center.x * viewport.pixelsPerUnit,
                          viewport.height * .5 + viewport.center.y * viewport.pixelsPerUnit};
    result.atoms.reserve(built.atomIds.size());
    for (unsigned int index = 0; index < built.atomIds.size(); ++index) {
        const auto rawPoint = drawer.getDrawCoords(index); const Point point{(rawPoint.x-viewLeft)*uniformScale,(rawPoint.y-viewTop)*uniformScale}; const Atom& atom = *molecule.atom(built.atomIds[index]);
        const double width = (atom.element == "C" && atom.alias.empty() ? 10.0 : std::max(18.0, 8.0 * static_cast<double>((atom.alias.empty() ? atom.element : atom.alias).size()))) * uniformScale;
        const double halfHeight = 9.0 * uniformScale;
        result.atoms.push_back({atom.id, point, {point.x - width * .5, point.y - halfHeight, point.x + width * .5, point.y + halfHeight}});
    }
    result.bonds.reserve(molecule.bonds.size());
    for (std::size_t index = 0; index < molecule.bonds.size(); ++index) {
        const Bond& bond = molecule.bonds[index];
        if(!bond.visible || !bond.alive)continue;
        const auto a = std::find_if(result.atoms.begin(), result.atoms.end(), [&](const AtomGeometry& value) { return value.id == bond.atomA; });
        const auto b = std::find_if(result.atoms.begin(), result.atoms.end(), [&](const AtomGeometry& value) { return value.id == bond.atomB; });
        if (a != result.atoms.end() && b != result.atoms.end()) {
            const Atom* modelA=molecule.atom(bond.atomA);const Atom* modelB=molecule.atom(bond.atomB);
            const double modelDx=modelB->position.x-modelA->position.x;
            const double modelDy=modelB->position.y-modelA->position.y;
            const double modelLength=std::max(1e-9,std::hypot(modelDx,modelDy));
            const Point modelTangent{modelDx/modelLength,modelDy/modelLength};
            const Point modelNormal{-modelTangent.y,modelTangent.x};
            const double modelHalfSpacing=style.doubleBondSpacing*referenceBondLength*.5;
            const auto extension=[&](const Atom* atom,bool first,double sign){
                if(!atom||(!atom->hidden&&(atom->element!="C"||!atom->alias.empty())))return 0.0;
                double best=0.0;
                for(const Bond& candidate:molecule.bonds){
                    if(candidate.id==bond.id||!candidate.alive||!candidate.visible||
                       (candidate.atomA!=atom->id&&candidate.atomB!=atom->id))continue;
                    const Atom* neighbour=molecule.atom(candidate.atomA==atom->id?candidate.atomB:candidate.atomA);
                    if(!neighbour||!neighbour->alive)continue;
                    const double ux=neighbour->position.x-atom->position.x,uy=neighbour->position.y-atom->position.y;
                    const double magnitude=std::hypot(ux,uy);if(magnitude<1e-9)continue;
                    const double un=(ux*modelNormal.x+uy*modelNormal.y)/magnitude;
                    const double ut=(ux*modelTangent.x+uy*modelTangent.y)/magnitude;
                    if(std::abs(un)<1e-6)continue;
                    const double ray=sign*modelHalfSpacing/un;
                    if(ray<=0.0||ray>modelLength*.35)continue;const double value=ray*ut;
                    if((first&&value>=-1e-6)||(!first&&value<=1e-6))continue;
                    if(best==0.0||std::abs(value)<std::abs(best))best=value;
                }
                return std::clamp(best,-modelLength*.25,modelLength*.25)*result.modelScale;
            };
            const double lineSpacing=style.doubleBondSpacing*referenceBondLength*result.modelScale;
            result.bonds.push_back({bond.id, a->center, b->center,
                                    bondHitPolygon(a->center, b->center, 7.0),
                                    bond.type, bond.secondaryLineSide, bond.stereo,
                                    lineSpacing,
                                    extension(modelA,true,-1.0),extension(modelA,true,1.0),
                                    extension(modelB,false,-1.0),extension(modelB,false,1.0)});
        }
    }
    drawer.finishDrawing(); result.svg = drawer.getDrawingText();
    unsigned labelIndex=0;
    for(const Atom& atom:molecule.atoms){if(!atom.alive)continue;const std::string pattern="(<path class='atom-"+std::to_string(labelIndex)+"'[^>]*fill=')#[0-9A-Fa-f]{6}('[^>]*)(/>)";const double opacity=std::clamp(atom.alpha*molecule.alpha/(255.0*255.0),0.0,1.0);result.svg=std::regex_replace(result.svg,std::regex(pattern),"$1"+hexColor(atom.color,molecule.color)+"$2 opacity='"+std::to_string(opacity)+"'$3");++labelIndex;}
    result.svg=std::regex_replace(result.svg,std::regex("<path class='bond-[^>]*?(?:/>|></path>)"),"");
    // MolDraw2D ACS output also emits small anonymous miter patches at
    // carbon junctions.  Once the classed RDKit bonds are replaced by our
    // explicit visual bonds these patches become detached black hooks.  Atom
    // glyphs carry atom-* classes, so anonymous paths can be removed safely
    // before inserting the authoritative explicit bond layer.
    // RDKit emits its anonymous junction patches before the classed atom
    // glyphs. Literal visual labels drawn after drawMolecule() are anonymous
    // paths too, so only clean the molecule prefix; removing anonymous paths
    // from the entire SVG would erase normal-number text such as X2.
    const std::size_t lastAtomClass = result.svg.rfind("class='atom-");
    if (lastAtomClass != std::string::npos) {
        const std::size_t lastAtomEnd = result.svg.find("/>", lastAtomClass);
        if (lastAtomEnd != std::string::npos) {
            std::string prefix = result.svg.substr(0, lastAtomEnd + 2);
            prefix = std::regex_replace(prefix,
                std::regex("<path(?![^>]*class=)[^>]*(?:/>|></path>)"), "");
            result.svg = prefix + result.svg.substr(lastAtomEnd + 2);
        }
    } else {
        result.svg=std::regex_replace(result.svg,
            std::regex("<path(?![^>]*class=)[^>]*(?:/>|></path>)"),"");
    }
    const std::string explicitBonds=explicitBondSvg(molecule,style,drawer);
    const std::string formalCharges=adornmentSvg(molecule,style,drawer);
    const std::size_t svgRoot=result.svg.find("<svg");
    const std::size_t rootEnd=svgRoot==std::string::npos?std::string::npos:result.svg.find('>',svgRoot);
    if(rootEnd!=std::string::npos)result.svg.insert(rootEnd+1,"\n<g id='explicit-visual-bonds'>\n"+explicitBonds+"</g>\n<g id='formal-charges'>\n"+formalCharges+"</g>\n");
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
    RDKit::RWMol flattened(*parsed);
    try { RDKit::MolOps::Kekulize(flattened, true); } catch (...) { flattened.updatePropertyCache(false); }
    RDKit::RWMol preparedForStereo(flattened);
    try {
        RDKit::MolDraw2DUtils::prepareMolForDrawing(preparedForStereo,
            /*kekulize=*/true, /*addChiralHs=*/false, /*wedgeBonds=*/true,
            /*forceCoords=*/false, /*wavyBonds=*/true);
    } catch (...) {
        preparedForStereo.updatePropertyCache(false);
    }
    Molecule result; result.id = stableId; result.name = name.empty() ? stableId : name; result.sourceSmiles = smiles;
    const double sourceBondLength=std::max(.01,RDKit::MolDraw2DUtils::meanBondLength(*parsed));
    constexpr double targetBondLength=32.0; const double coordinateScale=targetBondLength/sourceBondLength;
    std::vector<std::string> ids(parsed->getNumAtoms());
    for (unsigned int index = 0; index < parsed->getNumAtoms(); ++index) {
        const RDKit::Atom* source = parsed->getAtomWithIdx(index); const auto point = conformer.getAtomPos(index);
        std::uint64_t number = source->getAtomMapNum() ? source->getAtomMapNum() : result.nextAtomId++;
        std::string id = "A" + std::to_string(number); while (result.atom(id)) id = "A" + std::to_string(result.nextAtomId++);
        result.nextAtomId = std::max(result.nextAtomId, number + 1); ids[index] = id;
        result.atoms.push_back(Atom{.id=id, .creationSerial=static_cast<std::uint64_t>(index+1),
            .element=source->getSymbol(), .isotope=static_cast<int>(source->getIsotope()),
            .radicalElectrons=static_cast<int>(source->getNumRadicalElectrons()),
            .implicitHydrogens=static_cast<int>(source->getTotalNumHs(false)),
            .position={point.x*coordinateScale,point.y*coordinateScale}});
        if(source->getFormalCharge()!=0){const int charge=source->getFormalCharge();const std::string text=std::abs(charge)==1?(charge>0?"⊕":"⊖"):std::to_string(std::abs(charge))+(charge>0?"⊕":"⊖");result.adornments.push_back({"D"+std::to_string(result.nextAdornmentId++),static_cast<std::uint64_t>(parsed->getNumAtoms()+result.adornments.size()+1),id,text,{18.0,18.0},{},255,true});}
    }
    for (const RDKit::Bond* source : flattened.bonds()) {
        BondType type = source->getBondType() == RDKit::Bond::DOUBLE ? BondType::Double : source->getBondType() == RDKit::Bond::TRIPLE ? BondType::Triple : BondType::Single;
        const RDKit::Bond* depictedBond = preparedForStereo.getBondWithIdx(source->getIdx());
        BondStereo stereo = depictedBond->getBondDir() == RDKit::Bond::BEGINWEDGE ? BondStereo::SolidWedge : depictedBond->getBondDir() == RDKit::Bond::BEGINDASH ? BondStereo::DashedWedge : depictedBond->getBondDir() == RDKit::Bond::UNKNOWN ? BondStereo::Wavy : BondStereo::None;
        Bond bond{.id="B" + std::to_string(result.nextBondId++), .atomA=ids[source->getBeginAtomIdx()],
            .atomB=ids[source->getEndAtomIdx()], .type=type, .stereo=stereo};
        if(type==BondType::Double&&parsed->getRingInfo()->numBondRings(source->getIdx())>0){
            const Point a=result.atom(bond.atomA)->position,b=result.atom(bond.atomB)->position;
            Point centroid{};for(const Atom& atom:result.atoms){centroid.x+=atom.position.x;centroid.y+=atom.position.y;}centroid.x/=result.atoms.size();centroid.y/=result.atoms.size();
            const Point normal{-(b.y-a.y),b.x-a.x},mid{(a.x+b.x)*.5,(a.y+b.y)*.5};
            bond.secondaryLineSide=((centroid.x-mid.x)*normal.x+(centroid.y-mid.y)*normal.y)>=0?SecondaryLineSide::Left:SecondaryLineSide::Right;
        }
        result.bonds.push_back(std::move(bond));
    }
    result.referenceBondLength = targetBondLength;
    return result;
}

}  // namespace chem::core
