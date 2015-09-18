#!/usr/bin/env python
"""
This script runs multiple simulations to check sensitivity to parameters.
"""

from __future__ import division, print_function
import numpy as np
import pandas as pd
import os
from subprocess import call
import argparse

U_infty = 1.0
c = 1.0

def read_force_coeffs():
    """Read force coefficients from output file."""
    data = np.loadtxt("postProcessing/forceCoeffs/0/forceCoeffs.dat",
                      skiprows=9)
    return {"iterations": data.shape[0], "cl": data[-1, 3],
            "cd": data[-1, 2], "cm": data[-1, 1]}

def read_turbulence_fields():
    """Read sampled turbulence fields."""
    t = max(os.listdir("postProcessing/sets"))
    fp = "postProcessing/sets/{}/line_k_omega_epsilon.csv".format(t)
    df = pd.read_csv(fp)
    i = np.where(df.k == df.k.max())[0][0]
    return {"z_turbulence": df.z[i],
            "k": df.k[i],
            "omega": df.omega[i],
            "epsilon": df.epsilon[i]}

def set_Re(Re):
    """
    Set Reynolds number (to two significant digits) via kinematic viscosity in
    the input files.
    """
    print("Setting Reynolds number to {:.1e}".format(Re))
    nu = U_infty*c/Re
    nu = "{:.1e}".format(nu)
    with open("constant/transportProperties.template") as f:
        txt = f.read()
    with open("constant/transportProperties", "w") as f:
        f.write(txt.format(nu=nu))

def read_Re():
    """Read nu from the input files to calculate Reynolds number."""
    with open("constant/transportProperties") as f:
        for line in f.readlines():
            line = line.replace(";", "")
            line = line.split()
            if len(line) > 1 and line[0] == "nu":
                return U_infty*c/float(line[-1])

def read_yplus():
    """Read average yPlus from log.yPlus."""
    with open("log.yPlusRAS") as f:
        for line in f.readlines():
            line = line.split()
            try:
                if line[0] == "y+":
                    yplus = float(line[-1])
                    return yplus
            except IndexError:
                pass

def alpha_sweep(foil, start, stop, step, Re=2e5, append=False):
    """Vary the foil angle of attack and log results."""
    set_Re(Re)
    alpha_list = np.arange(start, stop, step)
    df_fname = "processed/NACA{}_{:.1e}.csv".format(foil, Re)
    if append:
        df = pd.read_csv(df_fname)
    else:
        df = pd.DataFrame(columns=["alpha_deg", "cl", "cd", "cm", "Re",
                                   "mean_yplus", "iterations", "k", "omega",
                                   "epsilon", "z_turbulence"])
    for alpha in alpha_list:
        call("./Allclean")
        call(["./Allrun", foil, str(alpha)])
        d = read_force_coeffs()
        d["alpha_deg"] = alpha
        #d.update(read_turbulence_fields())
        d["Re"] = read_Re()
        #d["mean_yplus"] = read_yplus()
        df = df.append(d, ignore_index=True)
        df.to_csv(df_fname, index=False)

def Re_alpha_sweep(foil, Re_start, Re_stop, Re_step, alpha_start, alpha_stop,
                   alpha_step):
    """Create a coefficient dataset for a list of Reynolds numbers."""
    pass

if __name__ == "__main__":
    if not os.path.isdir("processed"):
        os.mkdir("processed")

    parser = argparse.ArgumentParser(description="Vary the foil angle of \
                                     attack and log results.")
    parser.add_argument("start", type=int, help="Start angle of sweep.")
    parser.add_argument("stop", type=int, help="End angle of sweep. The sweep \
                        does not include this value.")
    parser.add_argument("step", nargs='?', type=int, default=1,
                        help="Spacing between values.")
    parser.add_argument("--foil", "-f", default="0012", help="Foil")
    parser.add_argument("--Reynolds", "-R", type=float, default=2e5,
                        help="Reynolds number")
    parser.add_argument("--append", "-a", action="store_true", default=False,
                        help="Append to previous results")
    args = parser.parse_args()

    alpha_sweep(args.foil, args.start, args.stop, args.step,
                Re=args.Reynolds, append=args.append)
