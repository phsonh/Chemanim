#include "Nodes.hpp"
#include "Timeline.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <cmath>
#include <map>
#include <set>
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

        definition("molecule_create", "新建分子", "分子", "对象", {field("target","分子","molecule","")}),
        definition("molecule_set_position", "设定分子坐标", "分子", "位置", {field("target","分子","molecule",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("molecule_lerp_position", "变换分子坐标", "分子", "位置", {field("target","分子","molecule",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_scale", "设定分子缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","缩放","float",1)}),
        definition("molecule_lerp_scale", "变换分子缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","目标缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_rotation", "设定分子旋转角度", "分子", "旋转", {field("target","分子","molecule",""),field("value","角度","float",0)}),
        definition("molecule_lerp_rotation", "变换分子旋转角度", "分子", "旋转", {field("target","分子","molecule",""),field("value","目标角度","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_alpha", "设定分子透明度", "分子", "颜色", {field("target","分子","molecule",""),field("value","Alpha","alpha",255)}),
        definition("molecule_lerp_alpha", "变换分子透明度", "分子", "颜色", {field("target","分子","molecule",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_color", "设定分子颜色", "分子", "分子对象", {field("target","分子","molecule",""),field("r","R","byte",255),field("g","G","byte",255),field("b","B","byte",255)}),
        definition("molecule_lerp_color", "变换分子颜色", "分子", "颜色", {field("target","分子","molecule",""),field("r","目标 R","byte",255),field("g","目标 G","byte",255),field("b","目标 B","byte",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_layer", "设定分子图层", "分子", "排列", {field("target","分子","molecule",""),field("value","层级","int",0)}),
        definition("molecule_set_visible", "设定可见", "分子", "分子对象", {field("target","分子","molecule",""),field("value","可见","bool",true)}),
        definition("molecule_delete", "删除分子", "分子", "分子对象", {field("target","分子","molecule","")}),

        definition("atom_set_xy", "设定原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("atom_lerp_xy", "插值原子坐标", "分子", "原子", {field("target","分子","molecule",""),field("atom","原子 ID","atom",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_lerp_pose", "插值姿态", "分子", "原子", {field("target","分子","molecule",""),field("pose","Pose","pose",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("atom_set_element", "设定显示文字", "分子", "原子", {field("target","分子","molecule",""),field("atom","顶点 ID","atom",""),field("value","文字","text","C")}),
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
        definition("merge_molecules", "合并分子", "分子", "对象", {field("target","主分子","molecule",""),field("source","并入分子","molecule",""),field("output","新分子","molecule","")}),
        definition("split_molecule", "分裂分子", "分子", "对象", {field("target","原分子","molecule",""),field("output","新分子","molecule","")}),

        definition("adornment_set_offset", "设定形式电荷坐标", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("x","本地 X","float",0),field("y","本地 Y","float",0)}),
        definition("adornment_lerp_offset", "插值形式电荷坐标", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("x","目标本地 X","float",0),field("y","目标本地 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("adornment_set_alpha", "设定形式电荷透明度", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("value","Alpha","alpha",255)}),
        definition("adornment_lerp_alpha", "插值形式电荷透明度", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("value","目标 Alpha","alpha",255),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("adornment_set_color", "设定形式电荷颜色", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("r","R","byte",0),field("g","G","byte",0),field("b","B","byte",0)}),
        definition("adornment_lerp_color", "插值形式电荷颜色", "分子", "形式电荷", {field("target","分子","molecule",""),field("adornment","形式电荷 ID","text",""),field("r","目标 R","byte",0),field("g","目标 G","byte",0),field("b","目标 B","byte",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),

        definition("arrow_new", "新建箭头", "箭头", "对象", {field("target","箭头名","arrow","arrow1")}),
        definition("arrow_delete", "删除箭头", "箭头", "对象", {field("target","箭头","arrow","")}),
        definition("arrow_set_curve", "设定箭头曲线", "箭头", "曲线", {field("target","箭头","arrow",""),field("x1","起点 X","float",0),field("y1","起点 Y","float",0),field("cx1","控制点 1 X","float",80),field("cy1","控制点 1 Y","float",80),field("cx2","控制点 2 X","float",-80),field("cy2","控制点 2 Y","float",80),field("x2","终点 X","float",160),field("y2","终点 Y","float",0)}),
        definition("arrow_set_position", "设定位置", "箭头", "变换", {field("target","箭头","arrow",""),field("x","X","float",0),field("y","Y","float",0)}),
        definition("arrow_lerp_position", "插值位置", "箭头", "变换", {field("target","箭头","arrow",""),field("x","目标 X","float",0),field("y","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_progress", "设定箭头绘制进度", "箭头", "绘制", {field("target","箭头","arrow",""),field("value","进度","float01",0)}),
        definition("arrow_lerp_progress", "变换箭头绘制进度", "箭头", "绘制", {field("target","箭头","arrow",""),field("value","目标进度","float01",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_alpha", "设定箭头透明度", "箭头", "颜色", {field("target","箭头","arrow",""),field("value","Alpha","alpha",255)}),
        definition("arrow_lerp_alpha", "变换箭头透明度", "箭头", "颜色", {field("target","箭头","arrow",""),field("value","目标 Alpha","alpha",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_color", "设定箭头颜色", "箭头", "颜色", {field("target","箭头","arrow",""),field("r","R","byte",25),field("g","G","byte",25),field("b","B","byte",25)}),
        definition("arrow_lerp_color", "变换箭头颜色", "箭头", "颜色", {field("target","箭头","arrow",""),field("r","目标 R","byte",25),field("g","目标 G","byte",25),field("b","目标 B","byte",25),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_set_width", "设定箭头线宽", "箭头", "线条", {field("target","箭头","arrow",""),field("value","线宽","float",3)}),

        definition("molecule_set_x", "设定分子横坐标", "分子", "位置", {field("target","分子","molecule",""),field("value","X","float",0)}),
        definition("molecule_set_y", "设定分子纵坐标", "分子", "位置", {field("target","分子","molecule",""),field("value","Y","float",0)}),
        definition("molecule_lerp_x", "变换分子横坐标", "分子", "位置", {field("target","分子","molecule",""),field("value","目标 X","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_lerp_y", "变换分子纵坐标", "分子", "位置", {field("target","分子","molecule",""),field("value","目标 Y","float",0),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_scale_x", "设定分子横向缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","横向缩放","float",1)}),
        definition("molecule_set_scale_y", "设定分子纵向缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","纵向缩放","float",1)}),
        definition("molecule_lerp_scale_x", "变换分子横向缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","目标横向缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_lerp_scale_y", "变换分子纵向缩放", "分子", "缩放", {field("target","分子","molecule",""),field("value","目标纵向缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_set_structure", "设定分子结构", "分子", "结构", {field("target","分子","molecule",""),field("snapshot","结构快照","multiline","{}")}),
        definition("molecule_lerp_structure", "变换分子结构形变", "分子", "结构", {field("target","分子","molecule",""),field("atoms","稳定原子坐标","multiline","{}"),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_gradient_structure", "渐变结构", "分子", "结构", {field("target","目标分子","molecule",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_merge_gradient_structure", "合并分子并变换结构", "分子", "结构", {field("target","主分子","molecule",""),field("source","并入分子","molecule",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_split_gradient_structure", "分裂分子并变换结构", "分子", "结构", {field("target","来源分子","molecule",""),field("destination","分出分子","molecule",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("selection_show", "变换分子选区显现", "分子", "结构", {field("target","分子","molecule",""),field("atoms","原子 ID","text",""),field("bonds","键 ID","text",""),field("adornments","标记 ID","text",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("selection_hide", "变换分子选区消失", "分子", "结构", {field("target","分子","molecule",""),field("atoms","原子 ID","text",""),field("bonds","键 ID","text",""),field("adornments","标记 ID","text",""),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("molecule_global_set_alpha", "设定全局分子透明度", "分子", "颜色", {field("value","Alpha","alpha",255)}),
        definition("molecule_global_set_color", "设定全局分子颜色", "分子", "颜色", {field("r","R","byte",255),field("g","G","byte",255),field("b","B","byte",255)}),
        definition("molecule_global_set_scale", "设定全局分子缩放", "分子", "缩放", {field("value","缩放","float",1)}),
        definition("molecule_global_set_scale_x", "设定全局分子横向缩放", "分子", "缩放", {field("value","横向缩放","float",1)}),
        definition("molecule_global_set_scale_y", "设定全局分子纵向缩放", "分子", "缩放", {field("value","纵向缩放","float",1)}),

        definition("arrow_set_scale", "设定箭头缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","缩放","float",1)}),
        definition("arrow_set_scale_x", "设定箭头横向缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","横向缩放","float",1)}),
        definition("arrow_set_scale_y", "设定箭头纵向缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","纵向缩放","float",1)}),
        definition("arrow_lerp_scale", "变换箭头缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","目标缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_lerp_scale_x", "变换箭头横向缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","目标横向缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_lerp_scale_y", "变换箭头纵向缩放", "箭头", "缩放", {field("target","箭头","arrow",""),field("value","目标纵向缩放","float",1),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_lerp_width", "变换箭头线宽", "箭头", "线条", {field("target","箭头","arrow",""),field("value","目标线宽","float",3),field("frames","帧数","int",30),field("easing","缓动","easing","linear")}),
        definition("arrow_global_set_alpha", "设定全局箭头透明度", "箭头", "颜色", {field("value","Alpha","alpha",255)}),
        definition("arrow_global_set_color", "设定全局箭头颜色", "箭头", "颜色", {field("r","R","byte",255),field("g","G","byte",255),field("b","B","byte",255)}),
        definition("arrow_global_set_scale", "设定全局箭头缩放", "箭头", "缩放", {field("value","缩放","float",1)}),
        definition("arrow_global_set_scale_x", "设定全局箭头横向缩放", "箭头", "缩放", {field("value","横向缩放","float",1)}),
        definition("arrow_global_set_scale_y", "设定全局箭头纵向缩放", "箭头", "缩放", {field("value","纵向缩放","float",1)}),
        definition("arrow_global_set_width", "设定全局箭头线宽", "箭头", "线条", {field("value","线宽","float",3)})
    });
    return value;
}

NodeMetadata metadata(std::string category,std::string scope,std::string section,int order,
                      std::string exposure,std::string targetKind,std::string capability="none",
                      bool duration=false,bool immutable=false,bool showSection=true) {
    return {std::move(category),std::move(scope),std::move(section),order,std::move(exposure),
            std::move(targetKind),std::move(capability),duration,immutable,showSection,{}};
}

const std::map<std::string,NodeMetadata>& metadataRegistry() {
    static const std::map<std::string,NodeMetadata> value = [] {
        std::map<std::string,NodeMetadata> m;
        const auto put=[&](const char* type,NodeMetadata value){m.emplace(type,std::move(value));};
        put("scene",metadata("通用","object","工程",0,"primary","scene"));
        put("wait",metadata("通用","object","时间",10,"primary","none"));
        put("raw_lua",metadata("通用","object","高级",90,"legacy","none"));
        put("molecule_create",metadata("分子","object","",0,"primary","molecule","none",false,true,false));
        put("molecule_delete",metadata("分子","object","",10,"primary","molecule","none",false,false,false));
        // merge_molecules retains hasDuration for pre-v8 compatibility nodes;
        // new object_v1 nodes are instantaneous and store frames=0.
        put("merge_molecules",metadata("分子","object","",20,"primary","molecule","none",true,false,false));
        put("split_molecule",metadata("分子","object","",30,"primary","molecule","none",false,false,false));
        const auto moleculeSet=[&](const char* type,const char* section,int order,const char* capability="none"){put(type,metadata("分子","set",section,order,"primary","molecule",capability));};
        moleculeSet("molecule_set_structure","结构",0,"snapshot");
        moleculeSet("molecule_set_position","位置",10);moleculeSet("molecule_set_x","位置",11);moleculeSet("molecule_set_y","位置",12);
        moleculeSet("molecule_set_scale","缩放",20);moleculeSet("molecule_set_scale_x","缩放",21);moleculeSet("molecule_set_scale_y","缩放",22);
        moleculeSet("molecule_set_rotation","旋转",30);moleculeSet("molecule_set_alpha","颜色",40);moleculeSet("molecule_set_color","颜色",41);moleculeSet("molecule_set_layer","排列",50);
        const auto moleculeTransform=[&](const char* type,const char* section,int order,const char* capability="none",bool immutable=false){put(type,metadata("分子","transform",section,order,"primary","molecule",capability,true,immutable));};
        moleculeTransform("molecule_gradient_structure","结构",0,"snapshot",true);
        moleculeTransform("molecule_lerp_position","位置",10);moleculeTransform("molecule_lerp_x","位置",11);moleculeTransform("molecule_lerp_y","位置",12);
        moleculeTransform("molecule_lerp_scale","缩放",20);moleculeTransform("molecule_lerp_scale_x","缩放",21);moleculeTransform("molecule_lerp_scale_y","缩放",22);
        moleculeTransform("molecule_lerp_rotation","旋转",30);moleculeTransform("molecule_lerp_alpha","颜色",40);moleculeTransform("molecule_lerp_color","颜色",41);
        const auto moleculeGlobal=[&](const char* type,const char* section,int order){put(type,metadata("分子","global",section,order,"primary","global_molecule"));};
        moleculeGlobal("molecule_global_set_alpha","颜色",0);moleculeGlobal("molecule_global_set_color","颜色",1);moleculeGlobal("molecule_global_set_scale","缩放",10);moleculeGlobal("molecule_global_set_scale_x","缩放",11);moleculeGlobal("molecule_global_set_scale_y","缩放",12);
        put("arrow_new",metadata("箭头","object","",0,"primary","arrow","none",false,false,false));put("arrow_delete",metadata("箭头","object","",10,"primary","arrow","none",false,false,false));
        const auto arrowSet=[&](const char* type,const char* section,int order){put(type,metadata("箭头","set",section,order,"primary","arrow"));};
        arrowSet("arrow_set_curve","曲线",0);arrowSet("arrow_set_progress","绘制",10);arrowSet("arrow_set_scale","缩放",20);arrowSet("arrow_set_scale_x","缩放",21);arrowSet("arrow_set_scale_y","缩放",22);arrowSet("arrow_set_alpha","颜色",30);arrowSet("arrow_set_color","颜色",31);arrowSet("arrow_set_width","线条",40);
        const auto arrowTransform=[&](const char* type,const char* section,int order){put(type,metadata("箭头","transform",section,order,"primary","arrow","none",true));};
        arrowTransform("arrow_lerp_progress","绘制",10);arrowTransform("arrow_lerp_scale","缩放",20);arrowTransform("arrow_lerp_scale_x","缩放",21);arrowTransform("arrow_lerp_scale_y","缩放",22);arrowTransform("arrow_lerp_alpha","颜色",30);arrowTransform("arrow_lerp_color","颜色",31);arrowTransform("arrow_lerp_width","线条",40);
        const auto arrowGlobal=[&](const char* type,const char* section,int order){put(type,metadata("箭头","global",section,order,"primary","global_arrow"));};
        arrowGlobal("arrow_global_set_alpha","颜色",0);arrowGlobal("arrow_global_set_color","颜色",1);arrowGlobal("arrow_global_set_scale","缩放",10);arrowGlobal("arrow_global_set_scale_x","缩放",11);arrowGlobal("arrow_global_set_scale_y","缩放",12);arrowGlobal("arrow_global_set_width","线条",20);
        // Hidden compatibility nodes retain execution and serialization.
        put("arrow_set_position",metadata("箭头","set","位置",90,"legacy","arrow"));
        put("arrow_lerp_position",metadata("箭头","transform","位置",90,"legacy","arrow","none",true));
        for(const char* type:{"atom_set_xy","atom_lerp_xy","atom_lerp_pose","atom_set_element","atom_set_alpha","atom_lerp_alpha","atom_set_color","atom_lerp_color","atom_set_hidden","bond_delete","bond_set_order","bond_set_secondary_side","bond_set_stereo","bond_set_visible","bond_set_alpha","bond_lerp_alpha","bond_set_color","bond_lerp_color","detach_subgraph","adornment_set_offset","adornment_lerp_offset","adornment_set_alpha","adornment_lerp_alpha","adornment_set_color","adornment_lerp_color"})
            if(!m.contains(type)) put(type,metadata("分子","set","兼容",900,"contextual","molecule"));
        for(const char* type:{"atom_lerp_xy","atom_lerp_pose","atom_lerp_alpha","atom_lerp_color","bond_lerp_alpha","bond_lerp_color","adornment_lerp_offset","adornment_lerp_alpha","adornment_lerp_color"})
            m.at(type).hasDuration=true;
        for(const char* type:{"molecule_lerp_structure","molecule_merge_gradient_structure","molecule_split_gradient_structure","bond_form","bond_break","selection_show","selection_hide","selection_fade"})
            put(type,metadata("分子","transform","兼容",900,"legacy","molecule","none",true));
        put("molecule_set_visible",metadata("分子","set","兼容",900,"legacy","molecule"));
        for(const char* type:{"molecule_set_position","molecule_lerp_position","molecule_set_x","molecule_lerp_x","molecule_set_y","molecule_lerp_y"})m.at(type).directManipulationCapability="molecule_translate";
        m.at("arrow_set_curve").directManipulationCapability="arrow_curve_handles";
        return m;
    }();
    return value;
}

const std::map<std::string,std::string>& toolLabels(){
    static const std::map<std::string,std::string> value={
        {"molecule_create","新建分子"},{"molecule_delete","删除分子"},{"merge_molecules","合并分子"},{"split_molecule","分裂分子"},
        {"molecule_global_set_alpha","透明度"},{"molecule_global_set_color","颜色"},{"molecule_global_set_scale","缩放"},{"molecule_global_set_scale_x","横向缩放"},{"molecule_global_set_scale_y","纵向缩放"},
        {"molecule_set_structure","分子结构"},{"molecule_set_position","坐标"},{"molecule_set_x","横坐标"},{"molecule_set_y","纵坐标"},{"molecule_set_scale","缩放"},{"molecule_set_scale_x","横向缩放"},{"molecule_set_scale_y","纵向缩放"},{"molecule_set_rotation","旋转角度"},{"molecule_set_alpha","透明度"},{"molecule_set_color","颜色"},{"molecule_set_layer","图层"},
        {"molecule_gradient_structure","渐变结构"},{"molecule_lerp_position","坐标"},{"molecule_lerp_x","横坐标"},{"molecule_lerp_y","纵坐标"},{"molecule_lerp_scale","缩放"},{"molecule_lerp_scale_x","横向缩放"},{"molecule_lerp_scale_y","纵向缩放"},{"molecule_lerp_rotation","旋转角度"},{"molecule_lerp_alpha","透明度"},{"molecule_lerp_color","颜色"},
        {"arrow_new","新建箭头"},{"arrow_delete","删除箭头"},{"arrow_global_set_alpha","透明度"},{"arrow_global_set_color","颜色"},{"arrow_global_set_scale","缩放"},{"arrow_global_set_scale_x","横向缩放"},{"arrow_global_set_scale_y","纵向缩放"},{"arrow_global_set_width","线宽"},
        {"arrow_set_curve","箭头曲线"},{"arrow_set_progress","绘制进度"},{"arrow_set_scale","缩放"},{"arrow_set_scale_x","横向缩放"},{"arrow_set_scale_y","纵向缩放"},{"arrow_set_alpha","透明度"},{"arrow_set_color","颜色"},{"arrow_set_width","线宽"},
        {"arrow_lerp_progress","绘制进度"},{"arrow_lerp_scale","缩放"},{"arrow_lerp_scale_x","横向缩放"},{"arrow_lerp_scale_y","纵向缩放"},{"arrow_lerp_alpha","透明度"},{"arrow_lerp_color","颜色"},{"arrow_lerp_width","线宽"}
    };return value;
}

json parseParams(const ScriptNode& node) {
    try { return json::parse(node.paramsJson); }
    catch (...) { return json::object(); }
}
int framesOf(const json& params) { return std::max(0, params.value("frames", 30)); }
bool hasDuration(std::string_view type) {
    return nodeMetadata(std::string(type)).hasDuration;
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

std::optional<Molecule> moleculeSnapshot(const json& snapshot) {
    if(!snapshot.is_object())return std::nullopt;
    try{
        json wrapper={{"format","chemanim-native-2d"},{"version",8},{"molecules",json::array({snapshot})},{"nodes",json::array()}};
        Project loaded=fromJson(wrapper.dump());if(!loaded.molecules.empty())return loaded.molecules.front();
    }catch(...){}
    return std::nullopt;
}

}  // namespace

Molecule blendMoleculeStructures(const Molecule& start,const Molecule& end,double progress) {
    const double t=std::clamp(progress,0.0,1.0);
    if(t<=0.0)return start;
    if(t>=1.0)return end;
    const auto byte=[&](double first,double second){return static_cast<int>(std::round(std::clamp(first+(second-first)*t,0.0,255.0)));};
    const auto point=[&](Point first,Point second){return Point{first.x+(second.x-first.x)*t,first.y+(second.y-first.y)*t};};
    const auto atomVisual=[](const Atom& a,const Atom& b){return a.element==b.element&&a.alias==b.alias&&a.labelSide==b.labelSide&&a.numberStyle==b.numberStyle&&a.isotope==b.isotope&&a.radicalElectrons==b.radicalElectrons&&a.implicitHydrogens==b.implicitHydrogens&&a.hidden==b.hidden;};
    const auto bondVisual=[](const Bond& a,const Bond& b){return a.atomA==b.atomA&&a.atomB==b.atomB&&a.type==b.type&&a.secondaryLineSide==b.secondaryLineSide&&a.stereo==b.stereo&&a.visible==b.visible;};
    const auto adornmentVisual=[](const AtomAdornment& a,const AtomAdornment& b){return a.atomId==b.atomId&&a.text==b.text;};
    Molecule result=end;result.atoms.clear();result.bonds.clear();result.adornments.clear();
    std::map<std::string,const Atom*> startAtoms,endAtoms;
    for(const Atom& value:start.atoms)if(value.alive)startAtoms[value.id]=&value;
    for(const Atom& value:end.atoms)if(value.alive)endAtoms[value.id]=&value;
    std::set<std::string> atomIds;for(const auto& [id,_]:startAtoms)atomIds.insert(id);for(const auto& [id,_]:endAtoms)atomIds.insert(id);
    for(const std::string& id:atomIds){
        const Atom* first=startAtoms.contains(id)?startAtoms.at(id):nullptr;const Atom* second=endAtoms.contains(id)?endAtoms.at(id):nullptr;
        if(first&&second){
            Atom current=*second;current.position=point(first->position,second->position);current.alpha=byte(first->alpha,second->alpha);current.color={byte(first->color.red,second->color.red),byte(first->color.green,second->color.green),byte(first->color.blue,second->color.blue)};
            if(atomVisual(*first,*second))result.atoms.push_back(std::move(current));
            else {current.alpha=static_cast<int>(std::round(second->alpha*t));result.atoms.push_back(std::move(current));Atom ghost=*first;ghost.id="__gradient_old_atom__"+id;ghost.position=point(first->position,second->position);ghost.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.atoms.push_back(std::move(ghost));}
        } else if(second){Atom current=*second;current.alpha=static_cast<int>(std::round(second->alpha*t));result.atoms.push_back(std::move(current));}
        else if(first){Atom current=*first;current.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.atoms.push_back(std::move(current));}
    }
    std::map<std::string,const Bond*> startBonds,endBonds;
    for(const Bond& value:start.bonds)if(value.alive)startBonds[value.id]=&value;
    for(const Bond& value:end.bonds)if(value.alive)endBonds[value.id]=&value;
    std::set<std::string> bondIds;for(const auto& [id,_]:startBonds)bondIds.insert(id);for(const auto& [id,_]:endBonds)bondIds.insert(id);
    for(const std::string& id:bondIds){
        const Bond* first=startBonds.contains(id)?startBonds.at(id):nullptr;const Bond* second=endBonds.contains(id)?endBonds.at(id):nullptr;
        if(first&&second){Bond current=*second;current.alpha=byte(first->alpha,second->alpha);current.color={byte(first->color.red,second->color.red),byte(first->color.green,second->color.green),byte(first->color.blue,second->color.blue)};if(bondVisual(*first,*second))result.bonds.push_back(std::move(current));else{current.alpha=static_cast<int>(std::round(second->alpha*t));result.bonds.push_back(std::move(current));Bond ghost=*first;ghost.id="__gradient_old_bond__"+id;ghost.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.bonds.push_back(std::move(ghost));}}
        else if(second){Bond current=*second;current.alpha=static_cast<int>(std::round(second->alpha*t));result.bonds.push_back(std::move(current));}
        else if(first){Bond current=*first;current.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.bonds.push_back(std::move(current));}
    }
    std::map<std::string,const AtomAdornment*> startAdornments,endAdornments;
    for(const AtomAdornment& value:start.adornments)if(value.alive)startAdornments[value.id]=&value;
    for(const AtomAdornment& value:end.adornments)if(value.alive)endAdornments[value.id]=&value;
    std::set<std::string> adornmentIds;for(const auto& [id,_]:startAdornments)adornmentIds.insert(id);for(const auto& [id,_]:endAdornments)adornmentIds.insert(id);
    for(const std::string& id:adornmentIds){
        const AtomAdornment* first=startAdornments.contains(id)?startAdornments.at(id):nullptr;const AtomAdornment* second=endAdornments.contains(id)?endAdornments.at(id):nullptr;
        if(first&&second){AtomAdornment current=*second;current.offset=point(first->offset,second->offset);current.alpha=byte(first->alpha,second->alpha);current.color={byte(first->color.red,second->color.red),byte(first->color.green,second->color.green),byte(first->color.blue,second->color.blue)};if(adornmentVisual(*first,*second))result.adornments.push_back(std::move(current));else{current.alpha=static_cast<int>(std::round(second->alpha*t));result.adornments.push_back(std::move(current));AtomAdornment ghost=*first;ghost.id="__gradient_old_adornment__"+id;ghost.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.adornments.push_back(std::move(ghost));}}
        else if(second){AtomAdornment current=*second;current.alpha=static_cast<int>(std::round(second->alpha*t));result.adornments.push_back(std::move(current));}
        else if(first){AtomAdornment current=*first;current.alpha=static_cast<int>(std::round(first->alpha*(1.0-t)));result.adornments.push_back(std::move(current));}
    }
    return result;
}

const NodeMetadata& nodeMetadata(const std::string& type) {
    static const NodeMetadata legacy=metadata("","object","兼容",999,"legacy","none");
    const auto found=metadataRegistry().find(type);
    return found==metadataRegistry().end()?legacy:found->second;
}

std::string nodeRegistryJson() {
    json exposed=registry();
    for(json& item:exposed) {
        const NodeMetadata& meta=nodeMetadata(item.value("type",""));
        item["category"]=meta.category.empty()?item.value("category",""):meta.category;
        item["scope"]=meta.scope;item["section"]=meta.section;item["order"]=meta.order;
        item["exposure"]=meta.exposure;item["target_kind"]=meta.targetKind;
        item["exposed"]=meta.exposure=="primary";
        item["structure_edit_capability"]=meta.structureEditCapability;
        item["has_duration"]=meta.hasDuration;item["target_immutable"]=meta.targetImmutable;
        item["show_section"]=meta.showSection;
        item["direct_manipulation_capability"]=meta.directManipulationCapability;
        if(const auto label=toolLabels().find(item.value("type",""));label!=toolLabels().end())item["tool_label"]=label->second;
    }
    return exposed.dump();
}

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

static EvaluatedScene evaluateNodesInternal(const Project& project, int frame,
                                             bool applyObjectVisualTransforms,
                                             bool preserveLocalObjectValues = false) {
    EvaluatedScene result;for(const Molecule& molecule:project.molecules)result.molecules.emplace(molecule.id,molecule);
    for(const ScriptNode& node:project.nodes)if(node.enabled&&node.type=="bond_form"){const json p=parseParams(node);auto found=result.molecules.find(targetOf(p));if(found!=result.molecules.end())if(Bond* bond=found->second.bond(p.value("bond",""))){bond->alive=false;bond->alpha=0;}}
    const auto timings=compileNodeTimings(project);std::map<std::string,NumberTrack> tracks;
    const auto track=[&](const std::string& key,double base)->NumberTrack&{auto [it,inserted]=tracks.try_emplace(key);if(inserted)it->second.base=base;return it->second;};
    const auto add=[&](const std::string& key,double base,int start,int duration,double target,Easing easing){track(key,base).add(start,duration,target,easing);};
    const auto addColor=[&](const std::string& prefix,Color base,const json& p,int start,int duration,Easing easing){add(prefix+":r",base.red,start,duration,p.value("r",base.red),easing);add(prefix+":g",base.green,start,duration,p.value("g",base.green),easing);add(prefix+":b",base.blue,start,duration,p.value("b",base.blue),easing);};
    std::set<std::string> explicitCreates;for(const ScriptNode& node:project.nodes)if(node.enabled&&node.type=="molecule_create")explicitCreates.insert(targetOf(parseParams(node)));
    if(!explicitCreates.empty())for(auto& [_,molecule]:result.molecules)molecule.visible=false;
    std::set<std::string> liveTargets=explicitCreates.empty()?std::set<std::string>{}:std::set<std::string>{};
    if(explicitCreates.empty())for(const auto& [id,_]:result.molecules)liveTargets.insert(id);
    std::map<std::string,int> createCounts;
    const auto diagnostic=[&](const ScriptNode& node,const std::string& message){result.diagnostics.push_back({node.id,"error",message});};
    const auto applyCapturedObject=[&](Molecule& output,const json& params)->bool{
        try{
            json snapshot=params.value("snapshot",json::object());if(snapshot.is_string())snapshot=json::parse(snapshot.get<std::string>());
            const auto loaded=moleculeSnapshot(snapshot);if(!loaded)return false;
            output.atoms=loaded->atoms;output.bonds=loaded->bonds;output.adornments=loaded->adornments;output.poses=loaded->poses;
            output.referenceBondLength=loaded->referenceBondLength;output.nextAtomId=std::max(output.nextAtomId,loaded->nextAtomId);
            output.nextBondId=std::max(output.nextBondId,loaded->nextBondId);output.nextAdornmentId=std::max(output.nextAdornmentId,loaded->nextAdornmentId);
            output.origin={params.value("origin_x",0.0),params.value("origin_y",0.0)};output.anchorInitialized=params.value("anchor_initialized",true);
            output.scaleX=params.value("scale_x",1.0);output.scaleY=params.value("scale_y",1.0);output.rotation=params.value("rotation",0.0);
            output.alpha=params.value("alpha",255);output.color={params.value("r",255),params.value("g",255),params.value("b",255)};
            output.layer=params.value("layer",0);output.visible=params.value("visible",true);output.retired=false;return true;
        }catch(...){return false;}
    };
    for(std::size_t index=0;index<project.nodes.size();++index){
        const ScriptNode& node=project.nodes[index];const NodeTiming& timing=timings[index];if(!node.enabled)continue;
        const json p=parseParams(node);const std::string target=targetOf(p);auto found=result.molecules.find(target);Molecule* molecule=found==result.molecules.end()?nullptr:&found->second;
        const int duration=hasDuration(node.type)?framesOf(p):0;const Easing easing=easingOf(p);
        const NodeMetadata& meta=nodeMetadata(node.type);
        if(node.type=="molecule_merge_gradient_structure"||node.type=="molecule_split_gradient_structure"){
            const char* key=node.type=="molecule_merge_gradient_structure"?"source":"destination";
            const std::string secondary=p.value(key,"");
            if(secondary.empty()||secondary==target||!result.molecules.contains(secondary)||!liveTargets.contains(secondary)){
                diagnostic(node,std::string(node.type=="molecule_merge_gradient_structure"?"并入分子":"分出分子")+"在该节点处无效: "+secondary);continue;
            }
        }
        if((node.type=="split_molecule"||(node.type=="merge_molecules"&&p.value("operation_version","")=="object_v1"))){
            const std::string output=p.value("output","");
            if(output.empty()||output==target||!result.molecules.contains(output)||!liveTargets.contains(output)){
                diagnostic(node,"新分子在该对象操作处无效: "+output);continue;
            }
            if(node.type=="merge_molecules"){
                const std::string source=p.value("source","");
                if(source.empty()||source==target||source==output||!result.molecules.contains(source)||!liveTargets.contains(source)){
                    diagnostic(node,"并入分子在该对象操作处无效: "+source);continue;
                }
            }
        }
        if(node.type=="molecule_create"){
            if(!molecule){diagnostic(node,"新建分子节点引用了不存在的分子 "+target);continue;}
            if(++createCounts[target]>1)diagnostic(node,"旧文件包含重复的新建分子节点；该节点按兼容语义保留");
            liveTargets.insert(target);if(frame>=timing.startFrame){molecule->visible=true;molecule->retired=false;}
        }
        else if((meta.targetKind=="molecule"||meta.targetKind=="arrow")&&target.empty()) {diagnostic(node,"节点缺少目标");continue;}
        else if(meta.targetKind=="molecule"&&(!molecule||!liveTargets.contains(target))) {diagnostic(node,"目标分子在该节点处尚未创建或已经删除: "+target);continue;}
        else if(meta.targetKind=="molecule"&&molecule&&p.contains("atom")&&!p.value("atom","").empty()&&!molecule->atom(p.value("atom",""))){diagnostic(node,"节点引用了已经消失的原子 "+p.value("atom",""));continue;}
        else if(meta.targetKind=="molecule"&&molecule&&p.contains("bond")&&!p.value("bond","").empty()&&node.type!="bond_form"&&node.type!="merge_molecules"&&!molecule->bond(p.value("bond",""))){diagnostic(node,"节点引用了已经消失的键 "+p.value("bond",""));continue;}
        else if(meta.targetKind=="molecule"&&molecule&&p.contains("adornment")&&!p.value("adornment","").empty()&&!molecule->adornment(p.value("adornment",""))){diagnostic(node,"节点引用了已经消失的标记 "+p.value("adornment",""));continue;}
        else if(node.type=="molecule_delete"&&molecule){if(frame>=timing.startFrame){molecule->visible=false;molecule->retired=true;}liveTargets.erase(target);}
        else if((node.type=="split_molecule"||(node.type=="merge_molecules"&&p.value("operation_version","")=="object_v1"))&&frame>=timing.startFrame){
            Molecule& output=result.molecules.at(p.value("output",""));
            if(!applyCapturedObject(output,p)){diagnostic(node,"对象操作缺少有效的结构快照");continue;}
            if(node.type=="merge_molecules"){
                Molecule& source=result.molecules.at(p.value("source",""));
                if(molecule){molecule->visible=false;molecule->retired=true;}source.visible=false;source.retired=true;
                liveTargets.erase(target);liveTargets.erase(source.id);
            }
        }
        else if((node.type=="molecule_set_position"||node.type=="molecule_lerp_position")&&molecule){if(const auto coordinate=molecule->coordinate()){add(target+":anchor:x",coordinate->x,timing.startFrame,duration,p.value("x",coordinate->x),easing);add(target+":anchor:y",coordinate->y,timing.startFrame,duration,p.value("y",coordinate->y),easing);}}
        else if((node.type=="molecule_set_x"||node.type=="molecule_lerp_x")&&molecule){if(const auto coordinate=molecule->coordinate())add(target+":anchor:x",coordinate->x,timing.startFrame,duration,p.value("value",coordinate->x),easing);}
        else if((node.type=="molecule_set_y"||node.type=="molecule_lerp_y")&&molecule){if(const auto coordinate=molecule->coordinate())add(target+":anchor:y",coordinate->y,timing.startFrame,duration,p.value("value",coordinate->y),easing);}
        else if((node.type=="molecule_set_scale"||node.type=="molecule_lerp_scale")&&molecule){add(target+":scale_x",molecule->scaleX,timing.startFrame,duration,p.value("value",1.0),easing);add(target+":scale_y",molecule->scaleY,timing.startFrame,duration,p.value("value",1.0),easing);}
        else if((node.type=="molecule_set_scale_x"||node.type=="molecule_lerp_scale_x")&&molecule)add(target+":scale_x",molecule->scaleX,timing.startFrame,duration,p.value("value",1.0),easing);
        else if((node.type=="molecule_set_scale_y"||node.type=="molecule_lerp_scale_y")&&molecule)add(target+":scale_y",molecule->scaleY,timing.startFrame,duration,p.value("value",1.0),easing);
        else if((node.type=="molecule_set_rotation"||node.type=="molecule_lerp_rotation")&&molecule)add(target+":rotation",molecule->rotation,timing.startFrame,duration,p.value("value",0.0),easing);
        else if((node.type=="molecule_set_alpha"||node.type=="molecule_lerp_alpha")&&molecule)add(target+":alpha",molecule->alpha,timing.startFrame,duration,p.value("value",255.0),easing);
        else if((node.type=="molecule_set_color"||node.type=="molecule_lerp_color")&&molecule)addColor(target+":color",molecule->color,p,timing.startFrame,duration,easing);
        else if(node.type=="molecule_set_structure"&&molecule&&frame>=timing.startFrame){
            try{json snapshot=p.value("snapshot",json::object());if(snapshot.is_string())snapshot=json::parse(snapshot.get<std::string>());if(const auto loaded=moleculeSnapshot(snapshot)){
                molecule->atoms=loaded->atoms;molecule->bonds=loaded->bonds;molecule->adornments=loaded->adornments;
                molecule->poses=loaded->poses;molecule->referenceBondLength=loaded->referenceBondLength;
                molecule->nextAtomId=std::max(molecule->nextAtomId,loaded->nextAtomId);
                molecule->nextBondId=std::max(molecule->nextBondId,loaded->nextBondId);
                molecule->nextAdornmentId=std::max(molecule->nextAdornmentId,loaded->nextAdornmentId);
            }else diagnostic(node,"分子结构快照不是有效的 v8 分子快照");}
            catch(...){diagnostic(node,"分子结构快照不是有效 JSON");}
        }
        else if(node.type=="molecule_gradient_structure"&&molecule&&frame>=timing.startFrame){
            try{
                const bool localSpace=p.value("coordinate_space","")=="molecule_local_v2";
                if(!localSpace){
                    result.diagnostics.push_back({node.id,"warning","旧渐变结构使用了显示坐标，需要重建终态"});
                    // Old b719729 snapshots contain already transformed display
                    // coordinates.  Preserve their legacy final-preview behaviour,
                    // but never feed those coordinates into a new local-space
                    // structure snapshot.
                    if(!applyObjectVisualTransforms)continue;
                }
                json startJson=p.value("start_snapshot",json::object()),endJson=p.value("end_snapshot",json::object());
                if(startJson.is_string())startJson=json::parse(startJson.get<std::string>());if(endJson.is_string())endJson=json::parse(endJson.get<std::string>());
                const auto start=moleculeSnapshot(startJson),end=moleculeSnapshot(endJson);
                if(!start||!end){diagnostic(node,"渐变结构缺少有效的起点或终点结构");continue;}
                if(p.value("needs_review",false))result.diagnostics.push_back({node.id,"warning","起点结构已变化，需要检查"});
                const double raw=duration<=0?1.0:static_cast<double>(frame-timing.startFrame)/duration;
                const Molecule blended=blendMoleculeStructures(*start,*end,easingValue(easing,raw));
                molecule->atoms=blended.atoms;molecule->bonds=blended.bonds;molecule->adornments=blended.adornments;
                molecule->poses=blended.poses;molecule->referenceBondLength=blended.referenceBondLength;
                molecule->nextAtomId=std::max(molecule->nextAtomId,end->nextAtomId);molecule->nextBondId=std::max(molecule->nextBondId,end->nextBondId);molecule->nextAdornmentId=std::max(molecule->nextAdornmentId,end->nextAdornmentId);
            }catch(...){diagnostic(node,"渐变结构快照不是有效 JSON");}
        }
        else if((node.type=="molecule_merge_gradient_structure"||node.type=="molecule_split_gradient_structure")&&molecule&&frame>=timing.startFrame){
            try{
                const bool merging=node.type=="molecule_merge_gradient_structure";
                const std::string secondaryId=p.value(merging?"source":"destination","");
                Molecule& secondary=result.molecules.at(secondaryId);
                const char* primaryStartKey=merging?"target_start_snapshot":"source_start_snapshot";
                const char* primaryEndKey=merging?"target_end_snapshot":"source_end_snapshot";
                const char* secondaryStartKey=merging?"source_start_snapshot":"destination_start_snapshot";
                const char* secondaryEndKey=merging?"source_end_snapshot":"destination_end_snapshot";
                const auto readSnapshot=[&](const char* key){json value=p.value(key,json::object());if(value.is_string())value=json::parse(value.get<std::string>());return moleculeSnapshot(value);};
                const auto primaryStart=readSnapshot(primaryStartKey),primaryEnd=readSnapshot(primaryEndKey),secondaryStart=readSnapshot(secondaryStartKey),secondaryEnd=readSnapshot(secondaryEndKey);
                if(!primaryStart||!primaryEnd||!secondaryStart||!secondaryEnd){diagnostic(node,"多分子结构变换缺少有效的局部结构快照");continue;}
                const double raw=duration<=0?1.0:static_cast<double>(frame-timing.startFrame)/duration;
                const double progress=easingValue(easing,raw);
                const Molecule primaryBlend=blendMoleculeStructures(*primaryStart,*primaryEnd,progress);
                const Molecule secondaryBlend=blendMoleculeStructures(*secondaryStart,*secondaryEnd,progress);
                molecule->atoms=primaryBlend.atoms;molecule->bonds=primaryBlend.bonds;molecule->adornments=primaryBlend.adornments;molecule->poses=primaryBlend.poses;molecule->referenceBondLength=primaryBlend.referenceBondLength;
                secondary.atoms=secondaryBlend.atoms;secondary.bonds=secondaryBlend.bonds;secondary.adornments=secondaryBlend.adornments;secondary.poses=secondaryBlend.poses;secondary.referenceBondLength=secondaryBlend.referenceBondLength;
                molecule->nextAtomId=std::max(molecule->nextAtomId,primaryEnd->nextAtomId);molecule->nextBondId=std::max(molecule->nextBondId,primaryEnd->nextBondId);molecule->nextAdornmentId=std::max(molecule->nextAdornmentId,primaryEnd->nextAdornmentId);
                secondary.nextAtomId=std::max(secondary.nextAtomId,secondaryEnd->nextAtomId);secondary.nextBondId=std::max(secondary.nextBondId,secondaryEnd->nextBondId);secondary.nextAdornmentId=std::max(secondary.nextAdornmentId,secondaryEnd->nextAdornmentId);
                if(merging&&frame>=timing.endFrame){secondary.retired=true;secondary.visible=false;liveTargets.erase(secondaryId);}
            }catch(...){diagnostic(node,"多分子结构变换快照不是有效 JSON");}
        }
        else if(node.type=="molecule_lerp_structure"&&molecule){
            try{json atoms=p.value("atoms",std::string("{}"));if(atoms.is_string())atoms=json::parse(atoms.get<std::string>());for(const auto& [id,value]:atoms.items())if(const Atom* atom=molecule->atom(id)){const std::string prefix=target+":atom:"+id;add(prefix+":x",atom->position.x,timing.startFrame,duration,value.value("x",atom->position.x),easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,value.value("y",atom->position.y),easing);}else diagnostic(node,"结构形变引用了已经消失的原子 "+id);}
            catch(...){diagnostic(node,"结构形变目标不是有效 JSON");}
        }
        else if(node.type=="molecule_global_set_alpha")add("global:molecule:alpha",255,timing.startFrame,0,p.value("value",255.0),easing);
        else if(node.type=="molecule_global_set_color"){add("global:molecule:r",255,timing.startFrame,0,p.value("r",255.0),easing);add("global:molecule:g",255,timing.startFrame,0,p.value("g",255.0),easing);add("global:molecule:b",255,timing.startFrame,0,p.value("b",255.0),easing);}
        else if(node.type=="molecule_global_set_scale"){add("global:molecule:scale_x",1,timing.startFrame,0,p.value("value",1.0),easing);add("global:molecule:scale_y",1,timing.startFrame,0,p.value("value",1.0),easing);}
        else if(node.type=="molecule_global_set_scale_x")add("global:molecule:scale_x",1,timing.startFrame,0,p.value("value",1.0),easing);
        else if(node.type=="molecule_global_set_scale_y")add("global:molecule:scale_y",1,timing.startFrame,0,p.value("value",1.0),easing);
        else if(node.type=="arrow_global_set_alpha")add("global:arrow:alpha",255,timing.startFrame,0,p.value("value",255.0),easing);
        else if(node.type=="arrow_global_set_color"){add("global:arrow:r",255,timing.startFrame,0,p.value("r",255.0),easing);add("global:arrow:g",255,timing.startFrame,0,p.value("g",255.0),easing);add("global:arrow:b",255,timing.startFrame,0,p.value("b",255.0),easing);}
        else if(node.type=="arrow_global_set_scale"){add("global:arrow:scale_x",1,timing.startFrame,0,p.value("value",1.0),easing);add("global:arrow:scale_y",1,timing.startFrame,0,p.value("value",1.0),easing);}
        else if(node.type=="arrow_global_set_scale_x")add("global:arrow:scale_x",1,timing.startFrame,0,p.value("value",1.0),easing);
        else if(node.type=="arrow_global_set_scale_y")add("global:arrow:scale_y",1,timing.startFrame,0,p.value("value",1.0),easing);
        else if(node.type=="arrow_global_set_width")add("global:arrow:width_override",-1,timing.startFrame,0,p.value("value",3.0),easing);
        else if(node.type=="molecule_set_layer"&&molecule&&frame>=timing.startFrame)molecule->layer=p.value("value",0);
        else if(node.type=="molecule_set_visible"&&molecule&&frame>=timing.startFrame)molecule->visible=p.value("value",true);
        else if((node.type=="atom_set_xy"||node.type=="atom_lerp_xy")&&molecule){if(const Atom* atom=molecule->atom(p.value("atom",""))){const std::string prefix=target+":atom:"+atom->id;add(prefix+":x",atom->position.x,timing.startFrame,duration,p.value("x",atom->position.x),easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,p.value("y",atom->position.y),easing);}}
        else if(node.type=="atom_lerp_pose"&&molecule){if(auto pose=molecule->poses.find(p.value("pose",""));pose!=molecule->poses.end())for(const auto& [atomId,point]:pose->second.atomPositions)if(const Atom* atom=molecule->atom(atomId)){const std::string prefix=target+":atom:"+atomId;add(prefix+":x",atom->position.x,timing.startFrame,duration,point.x,easing);add(prefix+":y",atom->position.y,timing.startFrame,duration,point.y,easing);}}
        else if(node.type=="atom_set_element"&&molecule&&frame>=timing.startFrame){if(Atom* atom=molecule->atom(p.value("atom","")))atom->alias=p.value("value","C");}
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
        else if((node.type=="selection_fade"||node.type=="selection_show"||node.type=="selection_hide")&&molecule){const double alpha=node.type=="selection_show"?255.0:node.type=="selection_hide"?0.0:p.value("value",0.0);for(const std::string& id:idList(p,"atoms"))if(const Atom* value=molecule->atom(id))add(target+":atom:"+id+":alpha",value->alpha,timing.startFrame,duration,alpha,easing);else diagnostic(node,"选区节点引用了已经消失的原子 "+id);for(const std::string& id:idList(p,"bonds"))if(const Bond* value=molecule->bond(id))add(target+":bond:"+id+":alpha",value->alpha,timing.startFrame,duration,alpha,easing);else diagnostic(node,"选区节点引用了已经消失的键 "+id);for(const std::string& id:idList(p,"adornments"))if(const AtomAdornment* value=molecule->adornment(id))add(target+":adornment:"+id+":alpha",value->alpha,timing.startFrame,duration,alpha,easing);}
        else if(node.type=="adornment_set_text"&&molecule&&frame>=timing.startFrame){if(AtomAdornment* value=molecule->adornment(p.value("adornment","")))value->text=p.value("value","⊕");}
        else if((node.type=="adornment_set_offset"||node.type=="adornment_lerp_offset")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment",""))){const std::string prefix=target+":adornment:"+value->id;add(prefix+":x",value->offset.x,timing.startFrame,duration,p.value("x",value->offset.x),easing);add(prefix+":y",value->offset.y,timing.startFrame,duration,p.value("y",value->offset.y),easing);}}
        else if((node.type=="adornment_set_alpha"||node.type=="adornment_lerp_alpha")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment","")))add(target+":adornment:"+value->id+":alpha",value->alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if((node.type=="adornment_set_color"||node.type=="adornment_lerp_color")&&molecule){if(const AtomAdornment* value=molecule->adornment(p.value("adornment","")))addColor(target+":adornment:"+value->id+":color",value->color,p,timing.startFrame,duration,easing);}
        else if(node.type=="detach_subgraph"&&molecule&&frame>=timing.startFrame){const std::string destination=p.value("destination","");if(!destination.empty()){Molecule& dest=result.molecules[destination];if(dest.id.empty()){dest.id=destination;dest.name=destination;dest.referenceBondLength=molecule->referenceBondLength;}const auto selectedAtoms=idList(p,"atoms");const std::set<std::string> atoms(selectedAtoms.begin(),selectedAtoms.end());const auto selectedBonds=idList(p,"bonds");const std::set<std::string> bonds(selectedBonds.begin(),selectedBonds.end());for(auto it=molecule->atoms.begin();it!=molecule->atoms.end();)if(atoms.contains(it->id)){dest.atoms.push_back(std::move(*it));it=molecule->atoms.erase(it);}else ++it;for(auto it=molecule->bonds.begin();it!=molecule->bonds.end();)if(bonds.contains(it->id)||(atoms.contains(it->atomA)&&atoms.contains(it->atomB))){dest.bonds.push_back(std::move(*it));it=molecule->bonds.erase(it);}else{if(atoms.contains(it->atomA)||atoms.contains(it->atomB))it->alive=false;++it;}for(auto it=molecule->adornments.begin();it!=molecule->adornments.end();)if(atoms.contains(it->atomId)){dest.adornments.push_back(std::move(*it));it=molecule->adornments.erase(it);}else ++it;}}
        else if(node.type=="merge_molecules"&&frame>=timing.startFrame){auto source=result.molecules.find(p.value("source",""));if(molecule&&source!=result.molecules.end()&&source->first!=target){molecule->atoms.insert(molecule->atoms.end(),std::make_move_iterator(source->second.atoms.begin()),std::make_move_iterator(source->second.atoms.end()));molecule->bonds.insert(molecule->bonds.end(),std::make_move_iterator(source->second.bonds.begin()),std::make_move_iterator(source->second.bonds.end()));molecule->adornments.insert(molecule->adornments.end(),std::make_move_iterator(source->second.adornments.begin()),std::make_move_iterator(source->second.adornments.end()));source->second.atoms.clear();source->second.bonds.clear();source->second.adornments.clear();source->second.retired=true;source->second.visible=false;const std::string bondId=p.value("bond","");if(!bondId.empty()&&molecule->atom(p.value("a",""))&&molecule->atom(p.value("b",""))){Bond created;created.id=bondId;created.atomA=p.value("a","");created.atomB=p.value("b","");created.type=orderOf(p.value("order","single"));created.alpha=0;molecule->bonds.push_back(created);add(target+":bond:"+bondId+":alpha",0,timing.startFrame,duration,255,easing);}}}
        else if(node.type=="arrow_new"){ArrowState& a=result.arrows[target];a.id=target;if(frame>=timing.startFrame)a.exists=true;}
        else if(node.type=="arrow_delete"){ArrowState& a=result.arrows[target];a.id=target;if(frame>=timing.startFrame)a.exists=false;}
        else if(node.type=="arrow_set_curve"&&frame>=timing.startFrame&&p.value("initialized",true)){ArrowState& a=result.arrows[target];a.id=target;a.start={p.value("x1",0.0),p.value("y1",0.0)};a.control1={p.value("cx1",80.0),p.value("cy1",80.0)};a.control2={p.value("cx2",-80.0),p.value("cy2",80.0)};a.end={p.value("x2",160.0),p.value("y2",0.0)};}
        else if(node.type=="arrow_set_position"||node.type=="arrow_lerp_position"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":x",a.position.x,timing.startFrame,duration,p.value("x",0.0),easing);add("arrow:"+target+":y",a.position.y,timing.startFrame,duration,p.value("y",0.0),easing);}
        else if(node.type=="arrow_set_progress"||node.type=="arrow_lerp_progress"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":progress",a.progress,timing.startFrame,duration,p.value("value",0.0),easing);}
        else if(node.type=="arrow_set_alpha"||node.type=="arrow_lerp_alpha"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":alpha",a.alpha,timing.startFrame,duration,p.value("value",255.0),easing);}
        else if(node.type=="arrow_set_color"||node.type=="arrow_lerp_color"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":r",a.red,timing.startFrame,duration,p.value("r",25.0),easing);add("arrow:"+target+":g",a.green,timing.startFrame,duration,p.value("g",25.0),easing);add("arrow:"+target+":b",a.blue,timing.startFrame,duration,p.value("b",25.0),easing);}
        else if(node.type=="arrow_set_scale"||node.type=="arrow_lerp_scale"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":scale_x",a.scaleX,timing.startFrame,duration,p.value("value",1.0),easing);add("arrow:"+target+":scale_y",a.scaleY,timing.startFrame,duration,p.value("value",1.0),easing);}
        else if(node.type=="arrow_set_scale_x"||node.type=="arrow_lerp_scale_x"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":scale_x",a.scaleX,timing.startFrame,duration,p.value("value",1.0),easing);}
        else if(node.type=="arrow_set_scale_y"||node.type=="arrow_lerp_scale_y"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":scale_y",a.scaleY,timing.startFrame,duration,p.value("value",1.0),easing);}
        else if(node.type=="arrow_set_width"||node.type=="arrow_lerp_width"){ArrowState& a=result.arrows[target];a.id=target;add("arrow:"+target+":width",a.width,timing.startFrame,duration,p.value("value",3.0),easing);}
    }
    const auto trackAt=[&](const char* key,double fallback){const auto found=tracks.find(key);return found==tracks.end()?fallback:found->second.at(frame);};
    result.globals.moleculeAlpha=trackAt("global:molecule:alpha",255);result.globals.moleculeRed=trackAt("global:molecule:r",255);result.globals.moleculeGreen=trackAt("global:molecule:g",255);result.globals.moleculeBlue=trackAt("global:molecule:b",255);result.globals.moleculeScaleX=trackAt("global:molecule:scale_x",1);result.globals.moleculeScaleY=trackAt("global:molecule:scale_y",1);
    result.globals.arrowAlpha=trackAt("global:arrow:alpha",255);result.globals.arrowRed=trackAt("global:arrow:r",255);result.globals.arrowGreen=trackAt("global:arrow:g",255);result.globals.arrowBlue=trackAt("global:arrow:b",255);result.globals.arrowScaleX=trackAt("global:arrow:scale_x",1);result.globals.arrowScaleY=trackAt("global:arrow:scale_y",1);result.globals.arrowWidth=trackAt("global:arrow:width_override",-1);
    const auto byte=[](double value){return static_cast<int>(std::round(std::clamp(value,0.0,255.0)));};
    for(auto& [id,molecule]:result.molecules){
        for(Atom& atom:molecule.atoms){const std::string p=id+":atom:"+atom.id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())atom.position.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())atom.position.y=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())atom.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())atom.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())atom.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())atom.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        for(Bond& bond:molecule.bonds){const std::string p=id+":bond:"+bond.id+":";if(auto it=tracks.find(p+"alpha");it!=tracks.end())bond.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())bond.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())bond.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())bond.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        for(AtomAdornment& value:molecule.adornments){const std::string p=id+":adornment:"+value.id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())value.offset.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())value.offset.y=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())value.alpha=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:r");it!=tracks.end())value.color.red=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:g");it!=tracks.end())value.color.green=static_cast<int>(std::round(it->second.at(frame)));if(auto it=tracks.find(p+"color:b");it!=tracks.end())value.color.blue=static_cast<int>(std::round(it->second.at(frame)));}
        if(!applyObjectVisualTransforms){
            // This is the authoritative molecule-local structure layer.  Object
            // position/scale/rotation and scene-global visual multipliers are
            // deliberately not baked into atom coordinates or molecule values.
            if(preserveLocalObjectValues){
                molecule.scaleX=tracks.contains(id+":scale_x")?tracks[id+":scale_x"].at(frame):molecule.scaleX;
                molecule.scaleY=tracks.contains(id+":scale_y")?tracks[id+":scale_y"].at(frame):molecule.scaleY;
                molecule.rotation=tracks.contains(id+":rotation")?tracks[id+":rotation"].at(frame):molecule.rotation;
                molecule.origin.x=tracks.contains(id+":anchor:x")?tracks[id+":anchor:x"].at(frame):molecule.origin.x;
                molecule.origin.y=tracks.contains(id+":anchor:y")?tracks[id+":anchor:y"].at(frame):molecule.origin.y;
                if(auto it=tracks.find(id+":alpha");it!=tracks.end())molecule.alpha=byte(it->second.at(frame));
                if(auto it=tracks.find(id+":color:r");it!=tracks.end())molecule.color.red=byte(it->second.at(frame));
                if(auto it=tracks.find(id+":color:g");it!=tracks.end())molecule.color.green=byte(it->second.at(frame));
                if(auto it=tracks.find(id+":color:b");it!=tracks.end())molecule.color.blue=byte(it->second.at(frame));
            }else{
                molecule.scaleX=1.0;molecule.scaleY=1.0;molecule.rotation=0.0;
                molecule.alpha=255;molecule.color={255,255,255};molecule.layer=0;
            }
            continue;
        }
        const double localScaleX=tracks.contains(id+":scale_x")?tracks[id+":scale_x"].at(frame):molecule.scaleX;const double localScaleY=tracks.contains(id+":scale_y")?tracks[id+":scale_y"].at(frame):molecule.scaleY;const double scaleX=localScaleX*result.globals.moleculeScaleX,scaleY=localScaleY*result.globals.moleculeScaleY;const double rotation=tracks.contains(id+":rotation")?tracks[id+":rotation"].at(frame):molecule.rotation;const Point baseOrigin=molecule.origin;const double desiredX=tracks.contains(id+":anchor:x")?tracks[id+":anchor:x"].at(frame):baseOrigin.x;const double desiredY=tracks.contains(id+":anchor:y")?tracks[id+":anchor:y"].at(frame):baseOrigin.y;const double radians=rotation*3.14159265358979323846/180.0,c=std::cos(radians),s=std::sin(radians);for(Atom& atom:molecule.atoms)if(atom.alive){const double x=atom.position.x*scaleX,y=atom.position.y*scaleY;atom.position={desiredX+x*c-y*s,desiredY+x*s+y*c};}molecule.origin={desiredX,desiredY};molecule.scaleX=scaleX;molecule.scaleY=scaleY;molecule.rotation=rotation;if(auto it=tracks.find(id+":alpha");it!=tracks.end())molecule.alpha=byte(it->second.at(frame));if(auto it=tracks.find(id+":color:r");it!=tracks.end())molecule.color.red=byte(it->second.at(frame));if(auto it=tracks.find(id+":color:g");it!=tracks.end())molecule.color.green=byte(it->second.at(frame));if(auto it=tracks.find(id+":color:b");it!=tracks.end())molecule.color.blue=byte(it->second.at(frame));molecule.alpha=byte(molecule.alpha*result.globals.moleculeAlpha/255.0);molecule.color.red=byte(molecule.color.red*result.globals.moleculeRed/255.0);molecule.color.green=byte(molecule.color.green*result.globals.moleculeGreen/255.0);molecule.color.blue=byte(molecule.color.blue*result.globals.moleculeBlue/255.0);
    }
    for(auto& [id,arrow]:result.arrows){const std::string p="arrow:"+id+":";if(auto it=tracks.find(p+"x");it!=tracks.end())arrow.position.x=it->second.at(frame);if(auto it=tracks.find(p+"y");it!=tracks.end())arrow.position.y=it->second.at(frame);if(auto it=tracks.find(p+"progress");it!=tracks.end())arrow.progress=it->second.at(frame);if(auto it=tracks.find(p+"alpha");it!=tracks.end())arrow.alpha=it->second.at(frame);if(auto it=tracks.find(p+"r");it!=tracks.end())arrow.red=it->second.at(frame);if(auto it=tracks.find(p+"g");it!=tracks.end())arrow.green=it->second.at(frame);if(auto it=tracks.find(p+"b");it!=tracks.end())arrow.blue=it->second.at(frame);if(auto it=tracks.find(p+"width");it!=tracks.end())arrow.width=it->second.at(frame);const double sx=(tracks.contains(p+"scale_x")?tracks[p+"scale_x"].at(frame):arrow.scaleX)*result.globals.arrowScaleX;const double sy=(tracks.contains(p+"scale_y")?tracks[p+"scale_y"].at(frame):arrow.scaleY)*result.globals.arrowScaleY;const Point origin=arrow.start;const auto scaled=[&](Point value){return Point{origin.x+(value.x-origin.x)*sx,origin.y+(value.y-origin.y)*sy};};arrow.control1=scaled(arrow.control1);arrow.control2=scaled(arrow.control2);arrow.end=scaled(arrow.end);arrow.scaleX=sx;arrow.scaleY=sy;arrow.alpha=std::clamp(arrow.alpha*result.globals.arrowAlpha/255.0,0.0,255.0);arrow.red=std::clamp(arrow.red*result.globals.arrowRed/255.0,0.0,255.0);arrow.green=std::clamp(arrow.green*result.globals.arrowGreen/255.0,0.0,255.0);arrow.blue=std::clamp(arrow.blue*result.globals.arrowBlue/255.0,0.0,255.0);if(result.globals.arrowWidth>=0)arrow.width=result.globals.arrowWidth;}
    return result;
}

EvaluatedScene evaluateNodes(const Project& project,int frame){
    return evaluateNodesInternal(project,frame,true);
}

EvaluatedScene evaluateLocalObjectNodes(const Project& project,int frame){
    return evaluateNodesInternal(project,frame,false,true);
}

EvaluatedScene evaluateStructureNodes(const Project& project,int frame){
    return evaluateNodesInternal(project,frame,false);
}

}  // namespace chem::core
