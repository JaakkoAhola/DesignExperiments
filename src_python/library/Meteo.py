# Functions extracting emulator and any other data from LES output NetCDF files,
# and collection of functions for generating LES inputs.
#
#    Tomi Raatikanen 18.1.2019
#
# Functions
# =========
# Use Python import to make these functions available, e.g. from LES2emu import GetEmuVars, get_netcdf_variable
#
# a) Functions for extracting data from the LES outputs
#    GetEmu2Vars(path)
#    GetEmu1Vars(fname,tstart,tend,[ttol,start_offset,end_offset])
#    get_netcdf_variable(fname,var_name,target_time,[end_time])
#    extract_write_data(fname_template,specs,[name_out,nmax])
#    get_netcdf_updraft(fname,tstart,tend,[ttol,tol_clw])
#
# b) Functions for generating LES inputs
#    calc_cloud_base(p_surf,theta,rw)
#    calc_lwc_altitude(p_surf,theta,rw,zz)
#    solve_rw(p_surf,theta,lwc,zz)
#    solve_rw_lwp(p_surf,theta,lwp,pblh)
#
# c) Helper functions
#    calc_psat_w(T)
#    calc_sat_mixr(p,T)
#    calc_rh(rw,T,press)
#
# Notes
# =====
# 1) Input file name should contain complete path in addition to the file name
#     e.g. '/ibrix/arch/ClimRes/aholaj/case_emulator_DESIGN_v1.4.0_LES_cray.dev20170324_LVL4/emul01/emul01.ts.nc'
# 2) Voima requires python 2.7.10, so execute "module load Python/2.7.10"
#

#
# LES inputs and outputs
#

def calc_cloud_base(p_surf, theta, rw):
    # Calulate cloud base heigh when liquid water potential temperature (theta [K]) and water
    # vapor mixing ratio (rw [kg/kg]) are constants. Surface pressure p_surf is given in Pa.
    # For more information, see "lifted condensation level" (LCL).
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    Rm = 461.5    # -||- for water
    ep2 = Rm / R - 1.0  # M_air/M_water-1
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    cpr = cp / R
    g = 9.8
    p00 = 1.0e+05
    #
    # Integrate to cloud base altitude
    dz = 1.            # 1 m resolution
    z = 0.                # The first altitude
    press = p_surf    # Start from surface
    RH = 0
    while RH < 100 and z < 10000:
        # Temperature (K)
        tavg = theta * (press / p00)**rcp
        #
        # Current RH (%)
        RH = calc_rh(rw, tavg, press)
        if RH > 100:
            break
        #
        # From z to z+dz
        z += dz
        # Virtual temperature: T_virtual=T*(1+ep2*rl)
        xsi = (1 + ep2 * rw)
        # Pressure (Pa)
        press -= g * dz * press / (R * tavg * xsi)
    #
    # No cloud
    if RH < 100:
        return -999
    #
    # Return cloud base altitude
    return z


def calc_lwc_altitude(p_surf, theta, rw, zz):
    # Calculate cloud water mixing ratio at a given altitude z (m) when liquid water potential
    # temperature (theta [k]) and water vapor mixing ratio (rw [kg/kg]) are constants.
    # Surface pressure p_surf is given in Pa.
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    Rm = 461.5    # -||- for water
    ep2 = Rm / R - 1.0  # M_air/M_water-1
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    cpr = cp / R
    g = 9.8
    p00 = 1.0e+05
    alvl = 2.5e+06  # ! latent heat of vaporization
    #
    # a) Integrate to cloud base altitude
    dz = 1.            # 1 m resolution
    z = 0.                # The first altitude
    press = p_surf    # Start from surface
    RH = 0
    while z < zz:
        # Temperature (K)
        tavg = theta * (press / p00)**rcp
        #
        # Current RH (%)
        RH = calc_rh(rw, tavg, press)
        if RH > 100:
            break
        #
        # From z to z+dz
        z += dz
        # Virtual temperature: T_virtual=T*(1+ep2*rl)
        xsi = (1 + ep2 * rw)
        # Pressure (Pa)
        press -= g * dz * press / (R * tavg * xsi)
    #
    # No cloud or cloud water
    if RH < 100:
        return 0.0
    #
    # b) Integrate up to given altitude
    while z < zz:
        # From z to z+dz
        z += dz
        #
        # Moist adiabatic lapse rate
        q_sat = calc_sat_mixr(press, tavg)
        tavg -= g * (1 + alvl * q_sat / (R * tavg)) / (cp + alvl**2 * q_sat / (Rm * tavg**2)) * dz
        #
        # New pressure
        xsi = (1 + ep2 * q_sat)
        press -= g * dz * press / (R * tavg * xsi)
    #
    # Return cloud water mixing ratio = totol - vapor
    return rw - q_sat


def solve_rw(p_surf, theta, lwc, zz):
    # Solve total water mixing ratio (rw, kg/kg) from surface pressure (p_surf, Pa), liquid water potential
    # temperature (theta, K) and liquid water mixing ratio (lwc) at altitude zz (m)
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    Rm = 461.5    # -||- for water
    ep2 = Rm / R - 1.0  # M_air/M_water-1
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    cpr = cp / R
    g = 9.8
    p00 = 1.0e+05
    alvl = 2.5e+06  # ! latent heat of vaporization
    #
    # Mimimum water vapor mixing ratio is at least lwc
    q_min = lwc
    #
    # Maximum water vapor mixing ratio is unlimited, but should be smaller
    # than that for a cloud which base is at surface
    t_surf = theta * (p_surf / p00)**rcp
    q_max = calc_sat_mixr(p_surf, t_surf)
    #
    k = 0
    while k < 100:
        q_new = (q_min + q_max) / 2
        lwc_calc = calc_lwc_altitude(p_surf, theta, q_new, zz)
        #
        if abs(lwc - lwc_calc) < 1e-7:
            break
        elif lwc < lwc_calc:
            q_max = q_new
        else:
            q_min = q_new
        k += 1
        # Failed
        if k == 50:
            return -999
    #
    return q_new


def calc_lwp(p_surf, theta, pblh, rt):
    # Calculate liquid water path (kg/m^2) when boundary layer liquid water potential temperature (theta [K]) and total
    # water mixing ratio (rt [kg/kg]) are constants from surface (p_surf, Pa) up to boundary layer top (pblh, Pa or km).
    # In addition to the liquid water path, function returns cloud base and top heights (m) and the maximum (or cloud top)
    # liquid water mixing ratio (kg/kg).
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    Rm = 461.5    # -||- for water
    ep2 = Rm / R - 1.0  # M_air/M_water-1
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    g = 9.8
    p00 = 1.0e+05
    alvl = 2.5e+06  # ! latent heat of vaporization
    #
    # It is assumed that a pblh value smaller than 10 is in kilometers and a value larger than that is Pa
    if pblh < 10.0:
        z_top = pblh * 1000.  # from km to m (above surface)
        p_top = 0.
    else:
        z_top = 10e3
        p_top = p_surf - pblh  # Pa (above surface)
    #
    # Outputs
    lwp = 0.    # Liquid water path (g/m^2)
    zb = -999.    # Cloud base height (m)
    zc = -999.    # Cloud top height (m)
    clw_max = 0.    # Maximum cloud liquid water
    #
    # a) Integrate to cloud base altitude
    dz = 1.            # 1 m resolution
    z = 0.                # The first altitude
    press = p_surf    # Start from surface
    RH = 0
    while press > p_top and z <= z_top:
        # Temperature (K)
        tavg = theta * (press / p00)**rcp
        #
        # Current RH (%)
        RH = calc_rh(rt, tavg, press)
        if RH > 100:
            zb = z
            break
        #
        # From z to z+dz
        z += dz
        # Virtual temperature: T_virtual=T*(1+ep2*rl)
        xsi = (1 + ep2 * rt)
        # Pressure (Pa)
        press -= g * dz * press / (R * tavg * xsi)
    #
    # No cloud or cloud water
    if RH <= 100:
        return lwp, zb, zc, clw_max
    zb = z
    #
    # b) Integrate up to the given altitude
    while press > p_top and z <= z_top:
        # From z to z+dz
        z += dz
        #
        # Moist adiabatic lapse rate
        # q_sat=calc_sat_mixr(press,tavg)
        q_sat = calc_sat_mixr(press, tavg)
        tavg -= g * (1 + alvl * q_sat / (R * tavg)) / (cp + alvl**2 * q_sat / (Rm * tavg**2)) * dz
        #
        # New pressure
        xsi = (1 + ep2 * q_sat)
        press -= g * dz * press / (R * tavg * xsi)
        #
        # Cloud water mixing ratio = totol - vapor
        rc = max(0., rt - q_sat)
        # LWP integral
        lwp += rc * dz * press / (R * tavg * xsi)
    #
    # Cloud top height
    zc = z
    clw_max = rc
    #
    # Return LWP (kg/m^2) and boundary layer height (m)
    return lwp, zb, zc, clw_max


def solve_rw_lwp(p_surf, theta, lwp, pblh, debug=False):
    # Solve boundary layer total water mixing ratio (kg/kg) from liquid water potential temperature (theta [K]),
    # liquid water path (lwp, kg/m^2) and boundary layer height (pblh, Pa or km) for an adiabatic cloud.
    # For example, solve_rw_lwp(101780.,293.,100e-3,20000.) would return 0.00723684088331 [kg/kg].
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    p00 = 1.0e+05
    #
    # LWP tolerance: 0.1 % but not more than 0.1e-3 kg/m^2 and not less than 1e-3 kg/kg
    tol = min(max(0.001 * lwp, 0.1e-3), 1e-3)
    #
    # Surface temperature (dry, i.e. no fog)
    t_surf = theta * (p_surf / p00)**rcp
    #
    # The highest LWP when RH=100% at the surface (no fog)
    rw_max = calc_sat_mixr(p_surf, t_surf)
    lwp_max, zb, zc, clw_max = calc_lwp(p_surf, theta, pblh, rw_max)
    # No fog cases
    if lwp_max < lwp:
        if debug:
            print(rf"Too high LWP: {lwp*1e3:5.1f} (g/m2),\
                        the maximum is {lwp_max*1e3:5.1f} (g/m2)\
            (theta = {theta:6.2f} (K), pblh={pblh/100.:3.0f} (hPa))")
        return -999.
    #
    # The lowest LWP when RH=0% at the surface
    rw_min = 0.
    lwp_min, zb, zc, clw_max = calc_lwp(p_surf, theta, pblh, rw_min)
    if lwp_min > lwp:
        if debug:
            print(rf"Too low LWP: {lwp*1e3:5.1f} (g/m2),\
                   the minimum is {lwp_max*1e3:5.1f} (g/m2)\
                   (theta={theta:6.2f} (K), pblh={pblh/100.:3.0f} (hPa))")
        return -999.
    #
    k = 0
    while k < 100:
        rw_new = (rw_min + rw_max) * 0.5
        lwp_new, zb, zc, clw_max = calc_lwp(p_surf, theta, pblh, rw_new)
        #
        if abs(lwp - lwp_new) < tol or abs(rw_max - rw_min) < 0.001e-3:
            return rw_new
        elif lwp < lwp_new:
            rw_max = rw_new
        else:
            rw_min = rw_new
        k += 1
    #
    # Failed
    if debug:
        print(rf"Iteration failed: \
              current LWP={lwp_new*1e3:5.1f},\
                  target LWP={lwp*1e3:5.1f}")
    return -999.


def solve_q_inv_RH(press, tpot, q, max_RH):
    # Function for adjusting total water mixing ratio so that the calculated RH will be no more
    # than the given RH limit. This function can be used to increase humidity inversion so that RH
    # above cloud is less than 100%. For this purpose the typical inputs are:
    #    press [Pa] = p_surf - pblh
    #    tpot [K] = tpot_pbl + tpot_inv
    #    q [kg/kg] = q_pbl - q_inv
    #    RH [%] = 98.
    #
    # Constants
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    cp = 1005.0    # Specific heat for a constant pressure
    rcp = R / cp
    p00 = 1.0e+05
    #
    # Temperature (K)
    temp = tpot * (press / p00)**rcp
    #
    # RH (%)
    rh = calc_rh(q, temp, press)
    #
    # All done if RH is not exceeding the RH limit
    if rh <= max_RH:
        return q, rh, rh
    #
    # Solve q so that RH=max_RH
    q_min = 0.
    q_max = q
    k = 0
    while k < 200:
        q_new = 0.5 * (q_min + q_max)
        rh_new = calc_rh(q_new, temp, press)
        #
        if abs(rh_new - max_RH) < 0.001:
            return q_new, rh_new, rh
        elif rh_new > max_RH:
            q_max = q_new
        else:
            q_min = q_new
        k += 1
    #
    # Failed
    print('Failed to solve water vapor mixing ratio from given RH!')
    return -999., -999., rh


#
#
#
# ================ Helper functions ================
#
def ls_fit(xx, yy):
    # Simple linear least squares fit: y=a+b*x
    import numpy
    #
    # Ignore NaN's
    x = []
    y = []
    i = 0
    for val in xx:
        if not (numpy.isnan(xx[i]) or numpy.isnan(yy[i])):
            x.append(xx[i])
            y.append(yy[i])
        i += 1
    #
    if len(x) <= 1:
        # Scalar
        a = 0.0
        a_std = 0.0
        b = 1.0
        b_std = 0.0
    else:
        # Matrix H
        H = numpy.matrix(numpy.vstack([numpy.ones(len(x)), x]).T)
        # LS solution
        th = numpy.linalg.inv(H.T * H) * H.T * numpy.matrix(y).T
        # Outputs
        a = numpy.asscalar(th[0])
        b = numpy.asscalar(th[1])
        # Parameter uncertainty
        if len(x) > 2:
            # Variance
            sv2 = ((numpy.matrix(y).T - H * th).T * (numpy.matrix(y).T - H * th)) / (len(x) - 2)
            std = numpy.sqrt(numpy.asscalar(sv2) * numpy.diagonal(numpy.linalg.inv(H.T * H)))
            # Outputs
            a_std = numpy.asscalar(std[0])
            b_std = numpy.asscalar(std[1])
        else:
            a_std = 0.0
            b_std = 0.0
    #
    return a, b, a_std, b_std,


def average_scaled(x, y):
    # Calculate average of x/y so that points where y=0 are ignored
    import numpy
    sx = 0.
    sx2 = 0.
    n = 0
    i = 0
    for yy in y:
        if yy > 0.:
            sx += x[i] / yy
            sx2 += (x[i] / yy)**2
            n += 1
        i += 1
    #
    if n == 0:
        return -999., -999.
    elif n == 1:
        return sx, -999.
    else:
        return sx / n, numpy.sqrt(sx2 / n - (sx / n)**2)

#
# Functions from the LES model
#


def calc_psat_w(T):
    # Function calculates the saturation vapor pressure (Pa) of liquid water as a function of temperature (K)
    #
    # thrm.f90:  real function rslf(p,t)
    c0 = 0.6105851e+03
    c1 = 0.4440316e+02
    c2 = 0.1430341e+01
    c3 = 0.2641412e-01
    c4 = 0.2995057e-03
    c5 = 0.2031998e-05
    c6 = 0.6936113e-08
    c7 = 0.2564861e-11
    c8 = -.3704404e-13
    #
    x = max(-80., T - 273.16)
    return c0 + x * (c1 + x * (c2 + x * (c3 + x * (c4 + x * (c5 + x * (c6 + x * (c7 + x * c8)))))))


def calc_sat_mixr(p, T):
    # Function calculates saturation mixing ratio for water (kg/kg)
    #
    # thrm.f90: real function rslf(p,t)
    #
    # r=m_w//m_air
    # R/Rm=287.04/461.5=.622
    #
    esl = calc_psat_w(T)
    return .622 * esl / (p - esl)


def calc_rh(rw, T, press):
    # Calculate RH (%) from water vapor mixing ratio rw (r=m_w/m_air [kg/kg]), temperature (K) and pressure (Pa)
    #
    # r=m_w//m_air=pw/Rm/(pair/R)=pw/(p-pw)*R/Rm => pw=p*r/(R/Rm+r)
    #
    R = 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
    Rm = 461.5    # Specific gas constant for water
    ep = R / Rm
    #
    psat = calc_psat_w(T)
    return press * rw / (ep + rw) / psat * 100
    # When ep>>rw => RH=press*rw/(ep*psat)*100
# ================================
