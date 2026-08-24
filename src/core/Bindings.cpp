#include "Depiction.hpp"
#include "Document.hpp"
#include "Editing.hpp"
#include "Nodes.hpp"
#include "Timeline.hpp"
#include "Codegen.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <filesystem>
#include <stdexcept>

namespace py = pybind11;
namespace core = chem::core;

namespace {
py::object jsonObject(const std::string& source) {
    return py::module_::import("json").attr("loads")(source);
}
std::filesystem::path pathFromUtf8(const std::string& value) {
    return std::filesystem::path(std::u8string(
        reinterpret_cast<const char8_t*>(value.data()), value.size()));
}

py::dict point(const core::Point& value) {
    py::dict result; result["x"] = value.x; result["y"] = value.y; return result;
}

py::dict hit(const core::Hit& value) {
    py::dict result;
    result["kind"] = value.kind == core::HitKind::Atom ? "atom" : value.kind == core::HitKind::Bond ? "bond" : "none";
    result["id"] = value.id; result["distance"] = value.distance; return result;
}

py::dict editResult(const core::EditResult& value) {
    py::dict result; result["changed"] = value.changed; result["message"] = value.message;
    result["hover"] = hit(value.hover); result["selected_atoms"] = value.selectedAtoms; result["selected_bonds"] = value.selectedBonds;
    static constexpr const char* previewNames[]={"none","rectangle","lasso","bond","ring","move","pan"};
    py::dict preview; preview["active"] = value.preview.active;preview["kind"]=previewNames[static_cast<int>(value.preview.kind)]; preview["start"] = point(value.preview.start); preview["current"] = point(value.preview.current);
    py::list polygon; for (const core::Point& item : value.preview.polygon) polygon.append(point(item)); preview["polygon"] = polygon;
    preview["snap_atom"] = value.preview.snapAtomId ? py::cast(*value.preview.snapAtomId) : py::none(); result["preview"] = preview;
    return result;
}

class CoreSession {
public:
    CoreSession() = default;

    void newProject() { session_.replaceProject({}); }
    void load(const std::string& path) { session_.replaceProject(core::loadProject(pathFromUtf8(path))); }
    void save(const std::string& path) const { core::saveProject(session_.project(), pathFromUtf8(path)); }
    std::string json() const { return core::toJson(session_.project()); }
    py::object project() const { return jsonObject(json()); }
    void replaceJson(const std::string& source) { session_.replaceProject(core::fromJson(source)); }
    std::string generateLua() const { return core::compileLua(session_.project()); }
    std::string writeMod(const std::string& root) const { return core::writeMod(session_.project(), std::filesystem::path(root)).string(); }

    std::string addBlankMolecule(const std::string& name) {
        const std::string id = session_.project().addBlankMolecule(name);
        session_.setActiveMolecule(id); return id;
    }
    std::string importSmiles(const std::string& name, const std::string& smiles) {
        const std::string id = session_.project().addBlankMolecule(name);
        *session_.project().molecule(id) = core::moleculeFromSmiles(id, name.empty() ? id : name, smiles);
        session_.setActiveMolecule(id); return id;
    }
    void setActiveMolecule(const std::string& id) { session_.setActiveMolecule(id); }
    std::string activeMolecule() const { return session_.activeMoleculeId(); }
    void setTool(const std::string& value) { session_.setTool(core::toolFromString(value)); }
    std::string tool() const { return core::toString(session_.tool()); }
    void setElement(const std::string& value) { session_.setElement(value); }
    void setViewport(int width, int height, double pixelsPerUnit, double centerX, double centerY) {
        session_.setViewport({width, height, pixelsPerUnit, {centerX, centerY}});
    }
    py::dict hitTest(double x, double y) const { return hit(session_.hitTest({x, y})); }
    py::dict pointerDown(double x, double y, bool alt, bool control, bool shift) { return editResult(session_.pointerDown({x,y},alt,control,shift)); }
    py::dict pointerMove(double x, double y, bool alt, bool control, bool shift) { return editResult(session_.pointerMove({x,y},alt,control,shift)); }
    py::dict pointerUp(double x, double y, bool alt, bool control, bool shift) { return editResult(session_.pointerUp({x,y},alt,control,shift)); }
    void cancelGesture() { session_.cancelGesture(); }
    bool deleteSelection() { return session_.deleteSelection(); }
    bool setAtomPosition(const std::string& id, double x, double y) { return session_.setAtomPosition(id,{x,y}); }
    bool setAtomElement(const std::string& id, const std::string& value) { return session_.setAtomElement(id,value); }
    bool changeAtomCharge(const std::string& id, int delta) { return session_.changeAtomCharge(id,delta); }
    bool canUndo() const { return session_.canUndo(); }
    bool canRedo() const { return session_.canRedo(); }
    bool undo() { return session_.undo(); }
    bool redo() { return session_.redo(); }
    void editBase(int frame) { session_.editBaseStructure(frame); }
    void previewTimeline(int frame) { session_.previewTimeline(frame); }
    void editNode(const std::string& id){session_.editScriptNode(id);}
    py::object nodeRegistry() const{return jsonObject(core::nodeRegistryJson());}
    py::list nodeTimings() const{py::list result;for(const auto& timing:core::compileNodeTimings(session_.project())){py::dict item;item["id"]=timing.id;item["type"]=timing.type;item["target"]=timing.target;item["start"]=timing.startFrame;item["end"]=timing.endFrame;item["enabled"]=timing.enabled;result.append(item);}return result;}
    std::string addNode(const std::string& type,const std::string& params,int index){return session_.addScriptNode(type,params,index<0?std::nullopt:std::optional<std::size_t>(static_cast<std::size_t>(index)));}
    bool updateNode(const std::string& id,const std::string& params){return session_.updateScriptNode(id,params);}
    bool enableNode(const std::string& id,bool enabled){return session_.setScriptNodeEnabled(id,enabled);}
    bool moveNode(const std::string& id,int index){return index>=0&&session_.moveScriptNode(id,static_cast<std::size_t>(index));}
    std::string duplicateNode(const std::string& id){return session_.duplicateScriptNode(id);}
    bool deleteNode(const std::string& id){return session_.deleteScriptNode(id);}
    bool updateScene(const std::string& value){return session_.updateScene(value);}
    int endFrame()const{return core::nodeSequenceEndFrame(session_.project());}
    py::dict evaluatedMolecules(int frame)const{py::dict result;for(const auto& [id,molecule]:core::evaluateNodes(session_.project(),frame).molecules){py::dict item;item["exists"]=true;item["visible"]=molecule.visible;item["x"]=molecule.scenePosition.x;item["y"]=molecule.scenePosition.y;item["scale"]=molecule.scale;item["rotation"]=molecule.rotation;item["alpha"]=molecule.alpha;item["layer"]=molecule.layer;result[py::str(id)]=item;}return result;}
    py::dict evaluatedArrows(int frame)const{py::dict result;for(const auto& [id,arrow]:core::evaluateNodes(session_.project(),frame).arrows){py::dict item;item["exists"]=arrow.exists;item["visible"]=arrow.visible;item["position"]=point(arrow.position);item["start"]=point(arrow.start);item["control1"]=point(arrow.control1);item["control2"]=point(arrow.control2);item["end"]=point(arrow.end);item["progress"]=arrow.progress;item["alpha"]=arrow.alpha;item["width"]=arrow.width;item["r"]=arrow.red;item["g"]=arrow.green;item["b"]=arrow.blue;result[py::str(id)]=item;}return result;}

    py::dict depict(bool finalEffect) {
        const core::Molecule molecule = session_.displayMolecule();
        const core::DepictionResult depiction = depiction_.depict(molecule, session_.project().style, session_.viewport());
        core::Viewport actual = session_.viewport();
        actual.pixelsPerUnit = depiction.modelScale;
        actual.center.x = (actual.width * .5 - depiction.modelOrigin.x) / depiction.modelScale;
        actual.center.y = (depiction.modelOrigin.y - actual.height * .5) / depiction.modelScale;
        session_.setViewport(actual);
        py::dict result; result["width"] = depiction.width; result["height"] = depiction.height; result["svg"] = depiction.svg;
        py::dict transform; transform["origin"] = point(depiction.modelOrigin); transform["pixels_per_unit"] = depiction.modelScale; result["transform"] = transform;
        py::list atoms; for (const auto& atom : depiction.atoms) { py::dict item; item["id"] = atom.id; item["center"] = point(atom.center); item["bounds"] = py::make_tuple(atom.labelBounds.left,atom.labelBounds.top,atom.labelBounds.right,atom.labelBounds.bottom); atoms.append(item); } result["atoms"] = atoms;
        py::list bonds; for (const auto& bond : depiction.bonds) { py::dict item; item["id"] = bond.id; item["first"] = point(bond.first); item["second"] = point(bond.second); py::list polygon; for (auto value : bond.hitPolygon) polygon.append(point(value)); item["hit_polygon"] = polygon; bonds.append(item); } result["bonds"] = bonds;
        if (finalEffect) { const auto raster = depiction_.rasterize(depiction); result["rgba"] = py::bytes(reinterpret_cast<const char*>(raster.rgba.data()), raster.rgba.size()); } else result["rgba"] = py::none();
        return result;
    }

    py::dict depictAt(int frame, bool finalEffect) const {
        const core::Molecule molecule = core::evaluateMolecule(session_.project(), session_.activeMoleculeId(), frame);
        const core::DepictionResult depiction = depiction_.depict(molecule, session_.project().style, session_.viewport());
        py::dict result; result["width"] = depiction.width; result["height"] = depiction.height; result["svg"] = depiction.svg;
        py::list atoms; for (const auto& atom : depiction.atoms) { py::dict item; item["id"] = atom.id; item["center"] = point(atom.center); atoms.append(item); } result["atoms"] = atoms;
        if (finalEffect) { const auto raster = depiction_.rasterize(depiction); result["rgba"] = py::bytes(reinterpret_cast<const char*>(raster.rgba.data()), raster.rgba.size()); } else result["rgba"] = py::none();
        return result;
    }

private:
    core::EditorSession session_;
    core::DepictionCore depiction_;
};
}  // namespace

PYBIND11_MODULE(chemanim_core, module) {
    module.doc() = "Shared Chemanim native 2D document, editing, timeline and ACS depiction core";
#ifdef CHEMANIM_BUILD_COMMIT
    module.attr("BUILD_COMMIT")=CHEMANIM_BUILD_COMMIT;
#else
    module.attr("BUILD_COMMIT")="unknown";
#endif
    module.attr("DOCUMENT_VERSION")=4;
    py::class_<CoreSession>(module, "CoreSession")
        .def(py::init<>()).def("new_project", &CoreSession::newProject).def("load", &CoreSession::load)
        .def("save", &CoreSession::save).def("json", &CoreSession::json).def("project", &CoreSession::project)
        .def("replace_json", &CoreSession::replaceJson).def("generate_lua", &CoreSession::generateLua).def("write_mod", &CoreSession::writeMod)
        .def("add_blank_molecule", &CoreSession::addBlankMolecule, py::arg("name")="")
        .def("import_smiles", &CoreSession::importSmiles).def("set_active_molecule", &CoreSession::setActiveMolecule)
        .def_property_readonly("active_molecule", &CoreSession::activeMolecule).def("set_tool", &CoreSession::setTool)
        .def_property_readonly("tool", &CoreSession::tool).def("set_element", &CoreSession::setElement)
        .def("set_viewport", &CoreSession::setViewport).def("hit_test", &CoreSession::hitTest)
        .def("pointer_down", &CoreSession::pointerDown, py::arg("x"),py::arg("y"),py::arg("alt")=false,py::arg("control")=false,py::arg("shift")=false)
        .def("pointer_move", &CoreSession::pointerMove, py::arg("x"),py::arg("y"),py::arg("alt")=false,py::arg("control")=false,py::arg("shift")=false)
        .def("pointer_up", &CoreSession::pointerUp, py::arg("x"),py::arg("y"),py::arg("alt")=false,py::arg("control")=false,py::arg("shift")=false)
        .def("cancel_gesture", &CoreSession::cancelGesture).def("delete_selection", &CoreSession::deleteSelection)
        .def("set_atom_position", &CoreSession::setAtomPosition).def("set_atom_element", &CoreSession::setAtomElement)
        .def("change_atom_charge", &CoreSession::changeAtomCharge).def_property_readonly("can_undo", &CoreSession::canUndo)
        .def_property_readonly("can_redo", &CoreSession::canRedo).def("undo", &CoreSession::undo).def("redo", &CoreSession::redo)
        .def("edit_base", &CoreSession::editBase, py::arg("frame")=0)
        .def("preview_timeline", &CoreSession::previewTimeline)
        .def("edit_node",&CoreSession::editNode)
        .def("node_registry",&CoreSession::nodeRegistry).def("node_timings",&CoreSession::nodeTimings)
        .def("add_node",&CoreSession::addNode,py::arg("type"),py::arg("params_json")="{}",py::arg("index")=-1)
        .def("update_node",&CoreSession::updateNode).def("enable_node",&CoreSession::enableNode).def("move_node",&CoreSession::moveNode)
        .def("duplicate_node",&CoreSession::duplicateNode).def("delete_node",&CoreSession::deleteNode).def("update_scene",&CoreSession::updateScene)
        .def_property_readonly("end_frame",&CoreSession::endFrame).def("evaluated_molecules",&CoreSession::evaluatedMolecules).def("evaluated_arrows",&CoreSession::evaluatedArrows)
        .def("depict", &CoreSession::depict, py::arg("final_effect")=false)
        .def("depict_at", &CoreSession::depictAt, py::arg("frame"), py::arg("final_effect")=false);
}
