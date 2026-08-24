#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <cstdint>
#include <string>

#include <rdkit/GraphMol/Conformer.h>
#include <rdkit/GraphMol/ROMol.h>

#include "schrodinger/sketcher/sketcher_widget.h"

namespace {
using schrodinger::sketcher::SketcherWidget;

SketcherWidget* widgetFrom(PyObject* value) {
    return static_cast<SketcherWidget*>(PyLong_AsVoidPtr(value));
}

PyObject* createWidget(PyObject*, PyObject*) {
    try {
        return PyLong_FromVoidPtr(new SketcherWidget());
    } catch (const std::exception& error) {
        PyErr_SetString(PyExc_RuntimeError, error.what());
        return nullptr;
    }
}

PyObject* loadAndInspect(PyObject*, PyObject* arguments) {
    PyObject* raw = nullptr;
    const char* smiles = nullptr;
    if (!PyArg_ParseTuple(arguments, "Os", &raw, &smiles)) return nullptr;
    SketcherWidget* widget = widgetFrom(raw);
    if (!widget || PyErr_Occurred()) return nullptr;
    try {
        widget->clear();
        widget->addFromString(std::string(smiles));
        const auto molecule = widget->getRDKitMolecule();
        if (!molecule) throw std::runtime_error("SketcherWidget returned no molecule");
        const bool hasConformer = molecule->getNumConformers() > 0;
        PyObject* positions = PyList_New(0);
        if (hasConformer) {
            const RDKit::Conformer& conformer = molecule->getConformer();
            for (unsigned int index = 0; index < molecule->getNumAtoms(); ++index) {
                const auto& point = conformer.getAtomPos(index);
                PyObject* coordinate = Py_BuildValue("(ddd)", point.x, point.y, point.z);
                PyList_Append(positions, coordinate);
                Py_DECREF(coordinate);
            }
        }
        PyObject* result = Py_BuildValue("{sI,sI,sO}",
            "atoms", molecule->getNumAtoms(),
            "conformers", molecule->getNumConformers(),
            "positions", positions);
        Py_DECREF(positions);
        return result;
    } catch (const std::exception& error) {
        PyErr_SetString(PyExc_RuntimeError, error.what());
        return nullptr;
    }
}

PyMethodDef methods[] = {
    {"create_widget", createWidget, METH_NOARGS, "Create a native SketcherWidget and return its pointer."},
    {"load_and_inspect", loadAndInspect, METH_VARARGS, "Load SMILES and return RDKit conformer information."},
    {nullptr, nullptr, 0, nullptr},
};

PyModuleDef module = {PyModuleDef_HEAD_INIT, "sketcher_probe", nullptr, -1, methods};
}  // namespace

PyMODINIT_FUNC PyInit_sketcher_probe() { return PyModule_Create(&module); }
