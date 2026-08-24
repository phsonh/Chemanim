# Schrödinger Sketcher integration validation

Validation was performed against Schrödinger Sketcher commit
`bbfa930e77c09545df165bc75e618bfe93396bbd`, with the same MSVC toolchain and
RDKit 2026.03.5 package used by Chemanim.

## Result

The full upstream `schrodinger_sketcher.dll` compiled successfully (including
its `SketcherWidget`). A small native Python module then:

1. created a C++ `SketcherWidget`;
2. wrapped the native pointer with `PyQt6.sip.wrapinstance`;
3. embedded it as the central widget of a PyQt6 `QMainWindow`;
4. loaded phenol; and
5. obtained a seven-atom RDKit molecule with one two-dimensional conformer and
   seven coordinate triples from C++.

The smoke process loaded PyQt6's Qt 6.11 runtime first and did not add another
Qt runtime directory. The probe and Sketcher therefore resolved against that
single loaded Qt 6 ABI; no second Qt DLL set was mixed into the process.

The probe source is in `tools/sketcher_integration_probe/`. Its successful
offscreen capture is written to
`media/correctness/sketcher_widget_probe.png`.

## Integration decision

Embedding the widget is technically feasible, but making the complete widget
the production editor would also import its separate molecule model, undo
stack and editing transaction layer. That conflicts with Chemanim's shared
C++ Core, stable IDs, `.cmm` and timeline contract. The current integration
therefore takes the narrower route allowed by the validation plan: port the
upstream tested direction placement and fragment/ring-side decisions into the
shared Core, retaining source comments and the BSD-3 notice.

This is a scoped decision, not a claim that the full widget can never be used.
The probe stays in the repository so the conclusion can be revisited without
repeating the ABI investigation.
