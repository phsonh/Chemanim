# Third-party notices

Chemanim 的原生二维编辑器使用 RDKit 生成二维坐标和 ACS 1996 风格 SVG。RDKit 采用 BSD 3-Clause License。项目没有复制 RDKit 源码或 Arial 字体；Python 依赖由 `tools/setup_editor.ps1` 安装，Arial 从 Windows 系统字体目录读取。

- RDKit: <https://github.com/rdkit/rdkit>
- License: <https://github.com/rdkit/rdkit/blob/master/license.txt>

C++ 第一阶段通过 NanoSVG 解析和光栅化由 RDKit 生成的 SVG。NanoSVG 在构建时由 CMake FetchContent 获取，采用 zlib License。

- NanoSVG: <https://github.com/memononen/nanosvg>
- License: <https://github.com/memononen/nanosvg/blob/master/LICENSE.txt>
