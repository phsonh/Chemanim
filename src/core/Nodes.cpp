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
        definition("molecule_set_color", "设定分子颜色", "分子", "分子对象", {field("target","分子","molecule",""),field("r","R","byte",255),field("g","G","byte",255),field("b","B","byte",255)}),
        definition("molecule_lerp_color", "插值分子颜色", "分子", "分子对象", {field("target","分子","molecule",""),field("r","目标 R","byte",255),field("g","目标 G","byte",255),field("b","目标 B","byte",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_layer", "设定层级", "分子", "分子对象", {field("target","分子","molecule",""),field("value","层级","int",0)}),
        definition("molecule_set_visible", "设定可见", "分子", "分子对象", {field("target","分子","molecule",""),field("value","可见","bool",true)}),
        definition("molecule_delete", "删除分子", "分子", "分子对象", {field("target","分子","molecule","")}),

        definition("atom_set_xy", "设定原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("atom_lerp_xy", "插值原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_lerp_pose", "插值姿态", "分子", "原子", {field("target","分子","molecule",""),field("pose","Pose","pose",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_set_element", "设定元素", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","元素","text","C")}),
        definition("atom_set_alpha", "设定原子透明度", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","Alpha","alpha",255)}),
        definition("atom_lerp_alpha", "插值原子透明度", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_set_color", "设定原子颜色", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("r","R","byte",0),field("g","G","byte",0),field("b","B","byte",0)}),
        definition("atom_lerp_color", "插值原子颜色", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("r","目标 R","byte",0),field("g","目标 G","byte",0),field("b","目标 B","byte",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_set_hidden", "设定原子隐藏", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("value","隐藏","bool",true)}),

        definition("bond_form", "形成键（淡入）", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("a","原子 A","atom",""),field("b","原子 B","atom",""),field("order","键型","bond_order","single"),field("secondary_line_side","双键副线","text","center"),field("stereo","立体","bond_stereo","none"),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("bond_break", "断键（淡出）", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("bond_delete", "删除键", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond","")}),
        definition("bond_set_order", "设定键级", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","键级","bond_order","single")}),
        definition("bond_set_secondary_side", "设定双键副线方向", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","方向","secondary_line_side","center")}),
        definition("bond_set_stereo", "设定键立体", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","立体","bond_stereo","none")}),
        definition("bond_set_visible", "设定键可见", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","可见","bool",true)}),
        definition("bond_set_alpha", "设定键透明度", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","Alpha","alpha",255)}),
        definition("bond_lerp_alpha", "插值键透明度", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("bond_set_color", "设定键颜色", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("r","R","byte",0),field("g","G","byte",0),field("b","B","byte",0)}),
        definition("bond_lerp_color", "插值键颜色", "分子", "键", {field("target","分子","molecule",""),field("bond","键 ID","bond",""),field("r","目标 R","byte",0),field("g","目标 G","byte",0),field("b","目标 B","byte",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),

        definition("selection_fade", "淡化选择内容", "分子", "视觉事件", {field("target","分子","molecule",""),field("atoms","原子 ID","text",""),field("bonds","键 ID","text",""),field("adornments","标记 ID","text",""),field("value","目标 Alpha","alpha",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("detach_subgraph", "分离子图", "分子", "视觉事件", {field("target","来源分子","molecule",""),field("destination","新分子","molecule",""),field("atoms","原子 ID","text",""),field("bonds","键 ID","text","")}),
        definition("merge_molecules", "合并分子", "分子", "视觉事件", {field("target","目标分子","molecule",""),field("source","来源分子","molecule",""),field("bond","新键 ID","text",""),field("a","原子 A","text",""),field("b","原子 B","text",""),field("order","键型","bond_order","single"),field("frames","新键淡入帧数","int",30),field("easing","缓动","easing","linear")}),

        definition("adornment_set_offset", "设定形式电荷坐标", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("x","本地 X","float",0),field("y","本地 Y","float",0)}),
        definition("adornment_lerp_offset", "插值形式电荷坐标", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("x","目标本地 X","float",0),field("y","目标本地 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("adornment_set_alpha", "设定形式电荷透明度", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("value","Alpha","alpha",255)}),
        definition("adornment_lerp_alpha", "插值形式电荷透明度", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("adornment_set_color", "设定形式电荷颜色", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("r","R","byte",0),field("g","G","byte",0),field("b","B","byte",0)}),
        definition("adornment_lerp_color", "插值形式电荷颜色", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("r","目标 R","byte",0),field("g","目标 G","byte",0),field("b","目标 B","byte",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),

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
bool hasDuration(std::string_view type) {
    return isLerp(type) || type == "selection_fade" || type == "bond_form" ||
           type == "bond_break" || type == "merge_molecules";
}
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
std::vector<std::string> idList(const json& params,const char* key){
    std::vector<std::string> result;const auto found=params.find(key);if(found==params.end())return result;
    if(found->is_array()){for(const json& value:*found)if(value.is_string())result.push_back(value.get<std::string>());return result;}
    std::string raw=found->is_string()?found->get<std::string>():"";std::size_t start=0;
    while(start<raw.size()){const std::size_t end=raw.find_first_of(", ;",start);const std::string value=raw.substr(start,end==std::string::npos?raw.size()-start:end-start);if(!value.empty())result.push_back(value);if(end==std::string::npos)break;start=end+1;}
    return result;
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
        else if(node.enabled && hasDuration(node.type)) end=cursor+framesOf(params);
        result.push_back({node.id,node.type,targetOf(params),cursor,end,node.enabled});
        if(node.enabled && node.type=="wait") cursor=end;
    }
    return result;
}

int nodeSequenceEndFrame(const Project& project) {
    int result=0; for(const NodeTiming& timing:compileNodeTimings(project)) result=std::max(result,timing.endFrame); return result;
}

EvaluatedScene evaluateNodes(const Project& project, int frame) {
    EvaluatedScene result;for(const Molecule& molecule:project.molecules)result.molecules.emplace(molecule.id,molecule);
    for(const ScriptNode& node:project.nodes)if(node.enabled&&node.type=="bond_form"){const json p=parseParams(node);auto found=result.molecules.find(targetOf(p));if(found!=result.molecules.end())if(Bond* bond=found->second.bond(p.value("bond",""))){bond->alive=false;bond->alpha=0;}}
    const auto timings=compileNodeTimings(project);std::map<std::string,NumberTrack> tracks;
    const auto track=[&](const std::string& key,double base)->NumberTrack&{auto [it,inserted]=tracks.try_emplace(key);if(inserted)it->second.base=base;return it->second;};
    const auto add=[&](const std::string& key,double base,int start,int duration,double target,Easing easing){track(key,base).add(start,duration,target,easing);};
    const auto addColor=[&](const std::string& prefix,Color base,const json& p,int start,int duration,Easing easing){add(prefix+":r",base.red,start,duration,p.value("r",base.red),easing);add(prefix+":g",base.green,start,duration,p.value("g",base.green),easing);add(prefix+":b",base.blue,start,duration,p.value("b",base.blue),easing);};
    std::set<std::string> explicitCreates;for(const ScriptNode& node:project.nodes)if(node.enabled&&node.type=="molecule_create")explicitCreates.insert(targetOf(parseParams(node)));
    if(!explicitCreates.empty())for(auto& [_,molecule]:result.molecules)molecule.visible=false;
    for(std::size_t index=0;index<project.nodes.size();++index){
        const ScriptNode& node=project.nodes[index];const NodeTiming& timing=timings[index];if(!node.enabled)continue;
        const json p=parseParams(node);const std::string target=targetOf(p);auto found=result.molecules.find(target);Molecule* molecule=found==result.molecules.end()?nullptr:&found->second;
        const int duration=hasDuration(node.type)?framesOf(p):0;const Easing easing=easingOf(p);
        if(node.type=="molecule_create"&&molecule&&frame>=timing.startFrame){molecule->visible=true;molecule->retired=false;}
        else if(node.type=="molecule_delete"&&molecule&&frame>=timing.startFrame){molecule->visible=false;molecule->retired=true;}
        else if((node.type=="molecule_set_position"||node.type=="molecule_lerp_position")&&molecule){if(const auto coordinate=molecule->coordinate()){add(target+":anchor:x",coordinate->x,timing.startFrame,duration,p.value("x",coordinate->x),easing);add(target+":anchor:y",coordinate->y,timing.startFrame,duration,p.value("y",coordinate->y),easing);}}
        else if((node.type=="molecule_set_scale"||node.type=="molecule_lerp_scale")&&molecule)add(target+":scale",molecule->scale,timing.startFrame,duration,p.value("value",1.0),easing);
        else if((node.type=="molecule_set_rotation"||node.type=="molecule_lerp_rotation")&&molecule)add(target+":rotation",molecule->rotation,timing.startFrame,duration,p.value("value",0.0),easing);
        else if((node.type=="molecule_set_alpha"||node.type=="molecule_lerp_alpha")&&molecule)add(target+":alpha",molecule->alpha,timing.startFrame,duration,p.value("value",255.0),easing);
        else if((node.type=="molecule_set_color"||node.type=="molecule_lerp_color")&&molecule)addColor(target+":color",molecule->color,p,timing.startFrame,duration,easing);
        else if(node.type=="molecule_set_layer"&&molecule&&frame>=timing.startFrame)molecule->layer=p.value("value",0);
        else if(node.type=="molecule_set_visible"&&molecule&&frame>=timing.startFrame)molecule->visible=p.value("value",true);
        else if((node.type=="atom_set_xy"||node.type=="atom_lerp_xy")&&molecule){if(const Atom* atom=molecule->atom(p.value("atom",""))){const std::string prefix=target+":atom:"+atom->id;add(prefix+":x",atom->position.x,timing.startFrame,duration,p.value("x",atom->position.x),easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,p.value("y",atom->position.y),easing);}}
        else if(node.type=="atom_lerp_pose"&&molecule){if(auto pose=molecule->poses.find(p.value("pose",""));pose!=molecule->poses.end())for(const auto& [atomId,point]:pose->second.atomPositions)if(const Atom* atom=molecule->atom(atomId)){const std::string prefix=target+":atom:"+atomId;add(prefix+":x",atom->position.x,timing.startFrame,duration,point.x,easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,point.y,easing);}}
        else if(node.type=="atom_set_element"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->element=p.value("value","C");}
        else if(node.type=="atom_set_hidden"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->hidden=p.value("value",true);}
        else if((node.type=="atom_set_alpha"||node.type=="atom_lerp_alpha")&&molecule){if(const Atom* atom=molecule->atom(p.value("atom","")))add(target+":atom:"+atom->id+":alpha",atom->alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if((node.type=="atom_set_color"||node.type=="atom_lerp_color")&&molecule){if(const Atom* atom=molecule->atom(p.value("atom","")))addColor(target+":atom:"+atom->id+":color",atom->color,p,timing.startFrame,duration,easing);}
        else if(node.type=="bond_form"&&molecule){const std::string bondId=p.value("bond","");Bond* bond=molecule->bond(bondId);if(!bond&&!bondId.empty()&&molecule->atom(p.value("a",""))&&molecule->atom(p.value("b",""))){Bond created;created.id=bondId;created.atomA=p.value("a","");created.atomB=p.value("b","");created.type=orderOf(p.value("order","single"));created.secondaryLineSide=secondaryLineSideFromString(p.value("secondary_line_side","center"));created.stereo=bondStereoFromString(p.value("stereo","none"));created.alpha=0;created.alive=false;molecule->bonds.push_back(std::move(created));bond=&molecule->bonds.back();}if(bond){add(target+":bond:"+bondId+":alpha",0,timing.startFrame,duration,255,easing);bond->alive=frame>=timing.startFrame;bond->visible=true;}}
        else if(node.type=="bond_break"&&molecule){if(Bond* bond=molecule->bond(p.value("bond",""))){add(target+":bond:"+bond->id+":alpha",bond->alpha,timing.startFrame,duration,0,easing);if(frame>=timing.endFrame)bond->alive=false;}}
        else if(node.type=="bond_delete"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->alive=false;}
        else if(node.type=="bond_set_order"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->type=orderOf(p.value("value","single"));}
        else if(node.type=="bond_set_secondary_side"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->secondaryLineSide=secondaryLineSideFromString(p.value("value","center"));}
        else if(node.type=="bond_set_stereo"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->stereo=bondStereoFromString(p.value("value","none"));}
        else if(node.type=="bond_set_visible"&&molecule&&frame>=timing.startFrame){if(Bond* bond=molecule->bond(p.value("bond","")))bond->visible=p.value("value",true);}
        else if((node.type=="bond_set_alpha"||node.type=="bond_lerp_alpha")&&molecule){if(const Bond* bond=molecule->bond(p.value("bond","")))add(target+":bond:"+bond->id+":alpha",bond->alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if((node.type=="bond_set_color"||node.type=="bond_lerp_color")&&molecule){if(const Bond* bond=molecule->bond(p.value("bond","")))addColor(target+":bond:"+bond->id+":color",bond->color,p,timing.startFrame,duration,easing);}
        else if(node.type=="selection_fade"&&molecule){for(const std::string& id:idList(p,"atoms"))if(const Atom* value=molecule->atom(id))add(target+":atom:"+id+":alpha",value->alpha,timing.startFrame,duration,p.value("value",0.0),easing);for(const std::string& id:idList(p,"bonds"))if(const Bond* value=molecule->bond(id))add(target+":bond:"+id+":alpha",value->alpha,timing.startFrame,duration,p.value("value",0.0),easing);for(const std::string& id:idList(p,"adornments"))if(const AtomAdornment* value=molecule->adornment(id))add(target+":adornment:"+id+":alpha",value->alpha,timing.startFrame,duration,p.value("value",0.0),easing);}
        else if(node.type=="adornment_set_text"&&molecule&&frame>=timing.startFrame){if(AtomAdornment* value=molecule->adornment(p.value("adornment","")))value->text=p.value("value","⊕");}
        else if((node.type=="adornment_set_offset"||node.type=="adornment_lerp_offset")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment",""))){const std::string prefix=target+":adornment:"+value->id;add(prefix+":x",value->offset.x,timing.startFrame,duration,p.value("x",value->offset.x),easing);add(prefix+":y",value->offset.y,timing.startFrame,duration,p.value("y",value->offset.y),easing);}}
        else if((node.type=="adornment_set_alpha"||node.type=="adornment_lerp_alpha")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment","")))add(target+":adornment:"+value->id+":alpha",value->alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if((node.type=="adornment_set_color"||node.type=="adornment_lerp_color")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment","")))addColor(target+":adornment:"+value->id+":color",value->color,p,timing.startFrame,duration,easing);}
        else if(node.type=="detach_subgraph"&&molecule&&frame>=timing.startFrame){const std::string destination=p.value("destination","");if(!destination.empty()){Molecule& dest=result.molecules[destination];if(dest.id.empty()){dest.id=destination;dest.name=destination;dest.referenceBondLength=molecule->referenceBondLength;}const auto selectedAtoms=idList(p,"atoms");const std::set<std::string> atoms(selectedAtoms.begin(),selectedAtoms.end());const auto selectedBonds=idList(p,"bonds");const std::set<std::string> bonds(selectedBonds.begin(),selectedBonds.end());for(auto it=molecule->atoms.begin();it!=molecule->atoms.end();)if(atoms.contains(it->id)){dest.atoms.push_back(std::move(*it));it=molecule->atoms.erase(it);}else ++it;for(auto it=molecule->bonds.begin();it!=molecule->bonds.end();)if(bonds.contains(it->id)||(atoms.contains(it->atomA)&&atoms.contains(it->atomB))){dest.bonds.push_back(std::move(*it));it=molecule->bonds.erase(it);}else{if(atoms.contains(it->atomA)||atoms.contains(it->atomB))it->alive=false;++it;}for(auto it=molecule->adornments.begin();it!=molecule->adornments.end();)if(atoms.contains(it->atomId)){dest.adornments.push_back(std::move(*it));it=molecule->adornments.erase(it);}else ++it;}}
        else if(node.type=="merge_molecules"&&frame>=timing.startFrame){auto source=result.molecules.find(p.value("source",""));if(molecule&&source!=result.molecules.end()&&source->first!=target){molecule->atoms.insert(molecule->atoms.end(),std::make_move_iterator(source->second.atoms.begin()),std::make_move_iterator(source->second.atoms.end()));molecule->bonds.insert(molecule->bonds.end(),std::make_move_iterator(source->second.bonds.begin()),std::make_move_iterator(source->second.bonds.end()));molecule->adornments.insert(molecule->adornments.end(),std::make_move_iterator(source->second.adornments.begin()),std::make_move_iterator(source->second.adornments.end()));source->second.atoms.clear();source->second.bonds.clear();source->second.adornments.clear();source->second.retired=true;source->second.visible=false;const std::string bondId=p.value("bond","");if(!bondId.empty()&&molecule->atom(p.value("a",""))&&molecule->atom(p.value("b",""))){Bond created;created.id=bondId;created.atomA=p.value("a","");created.atomB=p.value("b","");created.type=orderOf(p.value("order","single"));created.alpha=0;molecule->bonds.push_back(created);add(target+":bond:"+bondId+":alpha",0,timing.startFrame,duration,255,easing);}}}
        else if(node.type=="arrow_new"){ArrowState& a=result.arrows[target];a.id=target;if(frame>=timing.startFrame)a.exists=true;}
        else if(node.type=="arrow_delete"){ArrowState& a=result.arrows[target];a.id=target;if(frame>=timing.startFrame)a.exists=false;}
        else if(node.type=="arrow_set_curve"&&frame>=timing.startFrame){ArrowState& a=result.arrows[target];a.id=target;a.start={p.value("x1",0.0),p.value("y1",0.0)};a.control1={p.value("cx1",80.0),p.value("cy1",80.0)};a.control2={p.value("cx2",-80.0),p.value("cy2",80.0)};a.end={p.value("x2",160.0),p.value("y2",0.0)};}
        else if(node.type=="arrow_set_position"||node.type=="arrow_lerp_position"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":x",a.position.x,timing.startFrame,duration,p.value("x",0.0),easing);add("arrow:"+target+":y",a.position.y,timing.startFrame,duration,p.value("y",0.0),easing);}
        else if(node.type=="arrow_set_progress"||node.type=="arrow_lerp_progress"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":progress",a.progress,timing.startFrame,duration,p.value("value",0.0),easing);}
        else if(node.type=="arrow_set_alpha"||node.type=="arrow_lerp_alpha"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":alpha",a.alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if(node.type=="arrow_set_color"||node.type=="arrow_lerp_color"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":r",a.red,timing.startFrame,duration,p.value("r",25.0),easing);add("arrow:"+target+":g",a.green,timing.startFrame,duration,p.value("g",25.0),easing);add("arrow:"+target+":b",a.blue,timing.startFrame,duration,p.value("b",25.0),easing);}
        else if(node.type=="arrow_set_width"&&frame>=timing.startFrame){ArrowState& a=result.arrows[target];a.id=target;a.width=p.value("value",3.0);}
    }
    for(auto& [id,molecule]:result.molecules){
        for(Atom& atom:molecule.atoms){const std::string p=id+":atom:"+atom.id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())atom.position.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())atom.position.y=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())atom.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())atom.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())atom.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())atom.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        for(Bond& bond:molecule.bonds){const std::string p=id+":bond:"+bond.id+":";if(auto it=tracks.find(p+"alpha");it!=tracks.end())bond.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())bond.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())bond.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())bond.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        for(AtomAdornment& value:molecule.adornments){const std::string p=id+":adornment:"+value.id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())value.offset.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())value.offset.y=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())value.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())value.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())value.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())value.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        const double scale=tracks.contains(id+":scale")?tracks[id+":scale"].at(frame):molecule.scale;const double rotation=tracks.contains(id+":rotation")?tracks[id+":rotation"].at(frame):molecule.rotation;const auto anchor=molecule.coordinate();if(anchor){const double radians=rotation*3.14159265358979323846/180.0,c=std::cos(radians),s=std::sin(radians);for(Atom& atom:molecule.atoms)if(atom.alive){const double x=(atom.position.x-anchor->x)*scale,y=(atom.position.y-anchor->y)*scale;atom.position={anchor->x+x*c-y*s,anchor->y+x*s+y*c};}const double desiredX=tracks.contains(id+":anchor:x")?tracks[id+":anchor:x"].at(frame):anchor->x;const double desiredY=tracks.contains(id+":anchor:y")?tracks[id+":anchor:y"].at(frame):anchor->y;for(Atom& atom:molecule.atoms)if(atom.alive){atom.position.x+=desiredX-anchor->x;atom.position.y+=desiredY-anchor->y;}}molecule.scale=scale;molecule.rotation=rotation;if(auto it=tracks.find(id+":alpha");it!=tracks.end())molecule.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(id+":color:r");it!=tracks.end())molecule.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(id+":color:g");it!=tracks.end())molecule.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(id+":color:b");it!=tracks.end())molecule.color.blue=static_cast<int>(std::round(it->second.at(frame)));
    }
    for(auto& [id,arrow]:result.arrows){const std::string p="arrow:"+id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())arrow.position.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())arrow.position.y=it->second.at(frame);if(auto it=tracks.find(p+"progress");it!=tracks.end())arrow.progress=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())arrow.alpha=it->second.at(frame);if(auto it=tracks.find(p+"r");it!=tracks.end())arrow.red=it->second.at(frame);if(auto it=tracks.find(p+"g");it!=tracks.end())arrow.green=it->second.at(frame);if(auto it=tracks.find(p+"b");it!=tracks.end())arrow.blue=it->second.at(frame);}
    return result;
}

}  // namespace chem::core
