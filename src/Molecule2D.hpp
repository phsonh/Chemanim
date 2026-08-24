#pragma once

#include <string>
#include <vector>

namespace chem {

struct Vec2D {
    double x = 0.0;
    double y = 0.0;
};

struct Atom2D {
    std::string stableId;
    std::string element = "C";
    std::string alias;
    int isotope = 0;
    int formalCharge = 0;
    int radicalElectrons = 0;
    int implicitHydrogens = 0;
    bool aromatic = false;
    bool hidden = false;
    Vec2D position;
};

struct Bond2D {
    std::string stableId;
    std::string atomA;
    std::string atomB;
    double order = 1.0;
    bool aromatic = false;
    std::string stereo = "none";
    bool visible = true;
};

struct Molecule2D {
    std::string sourceSmiles;
    std::vector<Atom2D> atoms;
    std::vector<Bond2D> bonds;
};

} // namespace chem
