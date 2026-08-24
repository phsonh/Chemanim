# Third-party notices

Chemanim 的原生二维编辑器使用 RDKit 生成二维坐标和 ACS 1996 风格 SVG。RDKit 采用 BSD 3-Clause License。项目没有复制 RDKit 源码或 Arial 字体；Python 依赖由 `tools/setup_editor.ps1` 安装，Arial 从 Windows 系统字体目录读取。

- RDKit: <https://github.com/rdkit/rdkit>
- License: <https://github.com/rdkit/rdkit/blob/master/license.txt>

C++ 第一阶段通过 NanoSVG 解析和光栅化由 RDKit 生成的 SVG。NanoSVG 在构建时由 CMake FetchContent 获取，采用 zlib License。

- NanoSVG: <https://github.com/memononen/nanosvg>
- License: <https://github.com/memononen/nanosvg/blob/master/LICENSE.txt>

## Schrödinger 2D Sketcher geometry

Chemanim's deterministic bond-direction and placement helpers in
`src/core/SketcherGeometry.cpp` are adapted from:

- Repository: <https://github.com/schrodinger/sketcher>
- Fixed commit: `bbfa930e77c09545df165bc75e618bfe93396bbd`
- Original files:
  - `src/schrodinger/sketcher/tool/abstract_draw_atom_bond_scene_tool.cpp`
  - `src/schrodinger/sketcher/molviewer/coord_utils.cpp`
  - `src/schrodinger/sketcher/rdkit/fragment.cpp`
  - `test/schrodinger/sketcher/molviewer/test_coord_utils.cpp`
  - corresponding fragment/model tests under `test/schrodinger/sketcher/model/`

The angle increment is intentionally changed from the upstream default to 24
divisions per full turn, giving Chemanim 15° snapping. Chemanim retains its
own stable IDs, transactions, `.cmm` document and timeline.

BSD 3-Clause License

Copyright (c) 2024, Schrodinger, LLC - All Rights Reserved

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
