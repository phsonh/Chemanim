#include "Nodes.hpp"
#include "Timeline.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string_view>

namespace chem::core {
namespace {
using json = nlohmann::json;

json field(const char* key, const char* label, const char* kind, json value) {
    return {{"key", key}, {"label", label}, {"kind", kind}, {"default", std::move(value)}};
}
json definition(const char* type, const char* label, const char* category,
                const char* group, std::initializer_list<json> fields) {
    return {{"type", type}, {"label", label}, {"category", category},
            {"group", group}, {"fields", fields}};
}

const json& registry() {
    static const json value = json::array({
        definition("scene", "场景设置", "通用", "工程", {}),
        definition("wait", "等待", "通用", "时间", {field("frames","帧数","int",30)}),
        definition("raw_lua", "Lua 代码", "通用", "脚本", {field("code","Lua 代码","multiline","-- Lua code")} ),

        definition("molecule_create", "创建/引用分子", "分子", "分子对象", {field("target","分子","molecule","")}),
        definition("molecule_set_position", "设定位置", "分子", "分子对象", {field("target","分子","molecule",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("molecule_lerp_position", "插值位置", "分子", "分子对象", {field("target","分子","molecule",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_scale", "设定缩放", "分子", "分子对象", {field("target","分子","molecule",""),field("value","缩放","float",1)}),
        definition("molecule_lerp_scale", "插值缩放", "分子", "分子对象", {field("target","分子","molecule",""),field("value","目标缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_rotation", "设定旋转", "分子", "分子对象", {field("target","分子","molecule",""),field("value","角度","float",0)}),
        definition("molecule_lerp_rotation", "插值旋转", "分子", "分子对象", {field("target","分子","molecule",""),field("value","目标角度","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_alpha", "设定透明度", "分子", "分子对象", {field("target","分子","molecule",""),field("value","Alpha","alpha",255)}),
        definition("molecule_lerp_alpha", "插值透明度", "分子", "分子对象", {field("target","分子","molecule",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_layer", "设定层级", "分子", "分子对象", {field("target","分子","molecule",""),field("value","层级","int",0)}),
        definition("molecule_set_visible", "设定可见", "分子", "分子对象", {field("target","分子","molecule",""),field("value","可见","bool",true)}),
        definition("molecule_delete", "删除分子", "分子", "分子对象", {field("target","分子","molecule","")}),

        definition("atom_set_xy", "设定原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("atom_lerp_xy", "插值原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_lerp_pose", "插值姿态", "分子", "原子", {field("target","分子","molecule",""),field("pose","Pose","pose",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_set_element", "设定元素", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","元素","text","C")}),
        definition("atom_set_charge", "设定形式电荷", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","形式电荷","int",0)}),
        definition("atom_set_hidden", "设定原子隐藏", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","隐藏","bool",true)}),

        definition("bond_form", "形成键", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("a","原子 A","atom",""),field("b","原子 B","atom",""),field("order","键级","bond_order","single"),field("stereo","立体","bond_stereo","none")}),
        definition("bond_delete", "断开/删除键", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond","")}),
        definition("bond_set_order", "设定键级", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","键级","bond_order","single")}),
        definition("bond_set_stereo", "设定键立体", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","立体","bond_stereo","none")}),
        definition("bond_set_visible", "设定键可见", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","可见","bool",true)}),

        definition("arrow_new", "新建箭头", "箭头", "对象", {field("target","箭头名","arrow","arrow1")}),
        definition("arrow_delete", "删除箭头", "箭头", "对象", {field("target","箭头","arrow","")}),
        definition("arrow_set_curve", "设定曲线", "箭头", "曲线", {field("target","箭头","arrow",""),field("x1","起点 X","float",0),field("y1","起点 Y","float",0),field("cx1","控制点 1 X","float",80),field("cy1","控制点 1 Y","float",80),field("cx2","控制点 2 X","float",-80),field("cy2","控制点 2 Y","float",80),field("x2","终点 X","float",160),field("y2","终点 Y","float",0)}),
        definition("arrow_set_position", "设定位置", "箭头", "变换", {field("target","箭头","arrow",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("arrow_lerp_position", "插值位置", "箭头", "变换", {field("target","箭头","arrow",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_progress", "设定进度", "箭头", "显示", {field("target","箭头","arrow",""),field("value","进度","float01",0)}),
        definition("arrow_lerp_progress", "插值进度", "箭头", "显示", {field("target","箭头","arrow",""),field("value","目标进度","float01",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_alpha", "设定透明度", "箭头", "显示", {field("target","箭头","arrow",""),field("value","Alpha","alpha",255)}),
        definition("arrow_lerp_alpha", "插值透明度", "箭头", "显示", {field("target","箭头","arrow",""),field("value","目标 Alpha","alpha",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_color", "设定颜色", "箭头", "显示", {field("target","箭头","arrow",""),field("r","R","byte",25),field("g","G","byte",25),field("b","B","byte",25)}),
        definition("arrow_lerp_color", "插值颜色", "箭头", "显示", {field("target","箭头","arrow",""),field("r","目标 R","byte",25),field("g","目标 G","byte",25),field("b","目标 B","byte",25),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_width", "设定线宽", "箭头", "显示", {field("target","箭头","arrow",""),field("value","线宽","float",3)})
    });
    return value;
}

json parseParams(const ScriptNode& node) {
    try { return json::parse(node.paramsJson); }
    catch (...) { return json::object(); }
}
int framesOf(const json& params) { return std::max(0, params.value("frames", 30)); }
bool isLerp(std::string_view type) { return type.find("_lerp_") != std::string_view::npos; }
std::string targetOf(const json& params) { return params.value("target", ""); }

struct NumberSegment { int start=0, frames=0; double from=0, to=0; Easing easing=Easing::Linear; };
struct NumberTrack {
    double base=0;
    std::vector<NumberSegment> segments;
    double at(int frame) const {
        double value=base;
        for(const auto& segment:segments){
            if(frame<segment.start) break;
            const double t=segment.frames<=0?1.0:static_cast<double>(frame-segment.start)/segment.frames;
            value=segment.from+(segment.to-segment.from)*easingValue(segment.easing,t);
        }
        return value;
    }
    void add(int start,int frames,double target,Easing easing){
        const double from=at(start);
        // Evaluation is ordered.  A later segment owns this property from its
        // start onward, so old tails can never reappear.
        segments.push_back({start,frames,from,target,easing});
    }
};
Easing easingOf(const json& params) {
    const std::string value=params.value("easing","linear");
    if(value=="in_quad") return Easing::InQuad; if(value=="out_quad") return Easing::OutQuad;
    if(value=="in_out_quad") return Easing::InOutQuad; if(value=="smoothstep") return Easing::SmoothStep;
    if(value=="step") return Easing::Step; return Easing::Linear;
}

BondType orderOf(const std::string& value) { return bondTypeFromString(value); }
BondType stableDisplayForBond(const std::string& id) {
    unsigned value=0; for(const char ch:id) if(ch>='0'&&ch<='9') value=value*10+static_cast<unsigned>(ch-'0');
    return value%2==0?BondType::Double:BondType::Single;
}

}  // namespace

std::string nodeRegistryJson() { return registry().dump(); }

std::string defaultNodeParamsJson(const std::string& type) {
    for(const json& item:registry()) if(item.value("type","")==type){
        json result=json::object();
        for(const json& spec:item["fields"]) result[spec["key"].get<std::string>()]=spec["default"];
        return result.dump();
    }
    throw std::runtime_error("Unknown node type: "+type);
}

std::vector<NodeTiming> compileNodeTimings(const Project& project) {
    std::vector<NodeTiming> result; result.reserve(project.nodes.size()); int cursor=0;
    for(const ScriptNode& node:project.nodes){
        const json params=parseParams(node); int end=cursor;
        if(node.enabled && node.type=="wait") end=cursor+framesOf(params);
        else if(node.enabled && isLerp(node.type)) end=cursor+framesOf(params);
        result.push_back({node.id,node.type,targetOf(params),cursor,end,node.enabled});
        if(node.enabled && node.type=="wait") cursor=end;
    }
    return result;
}

int nodeSequenceEndFrame(const Project& project) {
    int result=0; for(const NodeTiming& timing:compileNodeTimings(project)) result=std::max(result,timing.endFrame); return result;
}

EvaluatedScene evaluateNodes(const Project& project, int frame) {
    EvaluatedScene result;
    for(const Molecule& molecule:project.molecules) result.molecules.emplace(molecule.id,molecule);
    const auto timings=compileNodeTimings(project);
    std::map<std::string,NumberTrack> tracks;
    const auto track=[&](const std::string& key,double base)->NumberTrack&{
        auto [it,inserted]=tracks.try_emplace(key); if(inserted) it->second.base=base; return it->second;
    };
    const auto add=[&](const std::string& key,double base,int start,int duration,double target,Easing easing){track(key,base).add(start,duration,target,easing);};
    std::set<std::string> explicitCreates;
    for(const ScriptNode& node:project.nodes) if(node.enabled&&node.type=="molecule_create") explicitCreates.insert(targetOf(parseParams(node)));
    if(!explicitCreates.empty()) for(auto& [id,molecule]:result.molecules) molecule.visible=false;

    for(std::size_t index=0;index<project.nodes.size();++index){
        const ScriptNode& node=project.nodes[index]; const NodeTiming& timing=timings[index];
        if(!node.enabled) continue; const json p=parseParams(node); const std::string target=targetOf(p);
        Molecule* molecule=nullptr; if(auto found=result.molecules.find(target);found!=result.molecules.end()) molecule=&found->second;
        const int duration=isLerp(node.type)?framesOf(p):0; const Easing easing=easingOf(p);
        if(node.type=="molecule_create"&&molecule&&frame>=timing.startFrame) molecule->visible=true;
        else if(node.type=="molecule_delete"&&molecule&&frame>=timing.startFrame) molecule->visible=false;
        else if(node.type=="molecule_set_position"||node.type=="molecule_lerp_position"){
            if(molecule){add(target+":x",molecule->scenePosition.x,timing.startFrame,duration,p.value("x",0.0),easing);add(target+":y",molecule->scenePosition.y,timing.startFrame,duration,p.value("y",0.0),easing);}
        } else if(node.type=="molecule_set_scale"||node.type=="molecule_lerp_scale") { if(molecule)add(target+":scale",molecule->scale,timing.startFrame,duration,p.value("value",1.0),easing); }
        else if(node.type=="molecule_set_rotation"||node.type=="molecule_lerp_rotation") { if(molecule)add(target+":rotation",molecule->rotation,timing.startFrame,duration,p.value("value",0.0),easing); }
        else if(node.type=="molecule_set_alpha"||node.type=="molecule_lerp_alpha") { if(molecule)add(target+":alpha",molecule->alpha,timing.startFrame,duration,p.value("value",255.0),easing); }
        else if(node.type=="molecule_set_layer"&&molecule&&frame>=timing.startFrame) molecule->layer=p.value("value",0);
        else if(node.type=="molecule_set_visible"&&molecule&&frame>=timing.startFrame) molecule->visible=p.value("value",true);
        else if((node.type=="atom_set_xy"||node.type=="atom_lerp_xy")&&molecule){
            if(const Atom* atom=molecule->atom(p.value("atom",""))){const std::string prefix=target+":atom:"+atom->id;add(prefix+":x",atom->position.x,timing.startFrame,duration,p.value("x",atom->position.x),easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,p.value("y",atom->position.y),easing);}
        } else if(node.type=="atom_lerp_pose"&&molecule){
            if(auto pose=molecule->poses.find(p.value("pose",""));pose!=molecule->poses.end())for(const auto& [atomId,point]:pose->second.atomPositions)if(const Atom* atom=molecule->atom(atomId)){const std::string prefix=target+":atom:"+atomId;add(prefix+":x",atom->position.x,timing.startFrame,duration,point.x,easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,point.y,easing);}
        } else if(node.type=="atom_set_element"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->element=p.value("value","C");}
        else if(node.type=="atom_set_charge"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->formalCharge=p.value("value",0);}
        else if(node.type=="atom_set_hidden"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->hidden=p.value("value",true);}
        else if(node.type=="bond_form"&&molecule&&frame>=timing.startFrame){
            const std::string bondId=p.value("bond",""); Bond* bond=molecule->bond(bondId);
            if(!bond&&!bondId.empty()&&molecule->atom(p.value("a",""))&&molecule->atom(p.value("b",""))){molecule->bonds.push_back({bondId,p.value("a",""),p.value("b",""),orderOf(p.value("order","single")),std::nullopt,bondStereoFromString(p.value("stereo","none")),true});bond=&molecule->bonds.back();}
            if(bond)bond->visible=true;
        } else if(node.type=="bond_delete"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->visible=false;}
        else if(node.type=="bond_set_order"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond",""))){bond->type=orderOf(p.value("value","single"));bond->displayType=bond->type==BondType::Aromatic?std::optional<BondType>(stableDisplayForBond(bond->id)):std::nullopt;}}
        else if(node.type=="bond_set_stereo"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->stereo=bondStereoFromString(p.value("value","none"));}
        else if(node.type=="bond_set_visible"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->visible=p.value("value",true);}
        else if(node.type=="arrow_new") { ArrowState& arrow=result.arrows[target]; arrow.id=target; if(frame>=timing.startFrame)arrow.exists=true; }
        else if(node.type=="arrow_delete") { ArrowState& arrow=result.arrows[target]; arrow.id=target; if(frame>=timing.startFrame)arrow.exists=false; }
        else if(node.type=="arrow_set_curve"&&frame>=timing.startFrame){ArrowState& a=result.arrows[target];a.id=target;a.start={p.value("x1",0.0),p.value("y1",0.0)};a.control1={p.value("cx1",80.0),p.value("cy1",80.0)};a.control2={p.value("cx2",-80.0),p.value("cy2",80.0)};a.end={p.value("x2",160.0),p.value("y2",0.0)};}
        else if(node.type=="arrow_set_position"||node.type=="arrow_lerp_position"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":x",a.position.x,timing.startFrame,duration,p.value("x",0.0),easing);add("arrow:"+target+":y",a.position.y,timing.startFrame,duration,p.value("y",0.0),easing);}
        else if(node.type=="arrow_set_progress"||node.type=="arrow_lerp_progress"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":progress",a.progress,timing.startFrame,duration,p.value("value",0.0),easing);}
        else if(node.type=="arrow_set_alpha"||node.type=="arrow_lerp_alpha"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":alpha",a.alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if(node.type=="arrow_set_color"||node.type=="arrow_lerp_color"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":r",a.red,timing.startFrame,duration,p.value("r",25.0),easing);add("arrow:"+target+":g",a.green,timing.startFrame,duration,p.value("g",25.0),easing);add("arrow:"+target+":b",a.blue,timing.startFrame,duration,p.value("b",25.0),easing);}
        else if(node.type=="arrow_set_width"&&frame>=timing.startFrame){ArrowState& a=result.arrows[target];a.id=target;a.width=p.value("value",3.0);}
    }
    for(auto& [id,molecule]:result.molecules){
        if(auto it=tracks.find(id+":x");it!=tracks.end())molecule.scenePosition.x=it->second.at(frame);
        if(auto it=tracks.find(id+":y");it!=tracks.end())molecule.scenePosition.y=it->second.at(frame);
        if(auto it=tracks.find(id+":scale");it!=tracks.end())molecule.scale=it->second.at(frame);
        if(auto it=tracks.find(id+":rotation");it!=tracks.end())molecule.rotation=it->second.at(frame);
        if(auto it=tracks.find(id+":alpha");it!=tracks.end())molecule.alpha=static_cast<int>(std::round(it->second.at(frame)));
        for(Atom& atom:molecule.atoms){const std::string prefix=id+":atom:"+atom.id;if(auto it=tracks.find(prefix+":x");it!=tracks.end())atom.position.x=it->second.at(frame);if(auto it=tracks.find(prefix+":y");it!=tracks.end())atom.position.y=it->second.at(frame);}
    }
    for(auto& [id,arrow]:result.arrows){const std::string p="arrow:"+id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())arrow.position.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())arrow.position.y=it->second.at(frame);if(auto it=tracks.find(p+"progress");it!=tracks.end())arrow.progress=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())arrow.alpha=it->second.at(frame);if(auto it=tracks.find(p+"r");it!=tracks.end())arrow.red=it->second.at(frame);if(auto it=tracks.find(p+"g");it!=tracks.end())arrow.green=it->second.at(frame);if(auto it=tracks.find(p+"b");it!=tracks.end())arrow.blue=it->second.at(frame);}
    return result;
}

}  // namespace chem::core
