calc_psat_w <- function(temperature){
  # Function calculates the saturation vapor pressure (Pa) of liquid water as a function of temperature (K)
  #
  # thrm.f90:  real function rslf(p,t)
  c0<-0.6105851e+03
  c1<-0.4440316e+02
  c2<-0.1430341e+01
  c3<-0.2641412e-01
  c4<-0.2995057e-03
  c5<-0.2031998e-05
  c6<-0.6936113e-08
  c7<-0.2564861e-11
  c8<- -0.3704404e-13
  #
  x<-max(-80.,temperature-273.16)
  calc_psat_w <- c0+x*(c1+x*(c2+x*(c3+x*(c4+x*(c5+x*(c6+x*(c7+x*c8)))))))
}

calc_rh <- function(rw,temperature,press){
  # Calculate RH (%) from water vapor mixing ratio rw (r=m_w/m_air [kg/kg]), temperature (K) and pressure (Pa)
  #
  # r=m_w//m_air=pw/Rm/(pair/R)=pw/(p-pw)*R/Rm => pw=p*r/(R/Rm+r)
  #
  R  <- 287.04	# Specific gas constant for dry air (R_specific=R/M), J/kg/K
  Rm <- 461.5	# Specific gas constant for water
  ep <- R/Rm
  #
  psat    <- calc_psat_w(temperature)
  calc_rh <- press*rw/(ep+rw)/psat*100
}


calc_sat_mixr <- function(p,temperature){
  # Function calculates saturation mixing ratio for water (kg/kg)
  #
  # thrm.f90: real function rslf(p,t)
  #
  # r=m_w//m_air
  # R/Rm=287.04/461.5=.622
  #
  esl<-calc_psat_w(temperature)
  calc_sat_mixr <- 0.622*esl/(p-esl)
}

calc_lwp <- function(p_surf, theta, pblh, rt){
  # Calculate liquid water path (kg/m^2) when boundary layer liquid water potential temperature (theta [K]) and total
  # water mixing ratio (rt [kg/kg]) are constants from surface (p_surf, Pa) up to boundary layer top (pblh, Pa or km).
  # In addition to the liquid water path, function returns cloud base and top heights (m) and the maximum (or cloud top)
  # liquid water mixing ratio (kg/kg).
  #
  # Constants
  R <- 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
  Rm <- 461.5    # -||- for water
  ep2 <- Rm/R-1.0 #M_air/M_water-1
  cp <- 1005.0    # Specific heat for a constant pressure
  rcp <- R/cp
  g <- 9.8
  p00 <- 1.0e+05
  alvl  <-  2.5e+06 #  ! latent heat of vaporization
  #
  # It is assumed that a pblh value smaller than 10 is in kilometers and a value larger than that is Pa
  if (pblh<10.0){
    z_top <- pblh*1000. # from km to m (above surface)
    p_top <- 0.
  }
  else{
    z_top <- 10e3
    p_top <- p_surf-pblh # Pa (above surface)
  }
  #
  # Outputs
  lwp <- 0.    # Liquid water path (g/m^2)
  zb <- -999.    # Cloud base height (m)
  zc <- -999.    # Cloud top height (m)
  clw_max <- 0.    # Maximum cloud liquid water
  #
  # a) Integrate to cloud base altitude
  dz <- 1.            # 1 m resolution
  z <- 0.                # The first altitude
  press <- p_surf    # Start from surface
  RH <- 0
  while (press>p_top & z<=z_top){
    # Temperature (K)
    tavg <-theta*(press/p00)**rcp
    #
    # Current RH (%)
    RH <-calc_rh(rt, tavg, press)
    if (RH>100){
      zb <-z
      break
    }
    #
    # From z to z+dz
    z <- z+dz
    # Virtual temperature: T_virtual=T*(1+ep2*rl)
    xsi <- (1+ep2*rt)
    # Pressure (Pa)
    press <- press-g*dz*press/(R*tavg*xsi)
  }
  #
  # No cloud or cloud water
  if (RH<=100){
    return (c(lwp, zb, zc, clw_max))
  }
  zb <-z
  #
  # b) Integrate up to the given altitude
  while (press>p_top & z<=z_top){
    # From z to z+dz
    z <- z + dz
    #
    # Moist adiabatic lapse rate
    #q_sat=calc_sat_mixr(press,tavg)
    q_sat <- calc_sat_mixr(press,tavg)
    tavg <- tavg - g*(1+alvl*q_sat/(R*tavg))/(cp+alvl**2*q_sat/(Rm*tavg**2))*dz
    #
    # New pressure
    xsi <-(1+ep2*q_sat)
    press <- press-g*dz*press/(R*tavg*xsi)
    #
    # Cloud water mixing ratio = totol - vapor
    rc <-max(0.,rt-q_sat)
    # LWP integral
    lwp <- lwp + rc*dz*press/(R*tavg*xsi)
  }
  #
  # Cloud top height
  zc <-z
  clw_max <-rc
  #
  # Return LWP (kg/m^2) and boundary layer height (m)
  return (c(lwp, zb, zc, clw_max))
}

solve_rw_lwp <- function (p_surf, theta, lwp, pblh, debug=False){
  # Solve boundary layer total water mixing ratio (kg/kg) from liquid water potential temperature (theta [K]),
  # liquid water path (lwp, kg/m^2) and boundary layer height (pblh, Pa or km) for an adiabatic cloud.
  # For example, solve_rw_lwp(101780.,293.,100e-3,20000.) would return 0.00723684088331 [kg/kg].
  #
  # Constants
  R  <- 287.04    # Specific gas constant for dry air (R_specific=R/M), J/kg/K
  cp  <- 1005.0    # Specific heat for a constant pressure
  rcp  <- R/cp
  p00  <- 1.0e+05
  #
  # LWP tolerance: 0.1 % but not more than 0.1e-3 kg/m^2 and not less than 1e-3 kg/kg
  tol  <- min(max(0.001*lwp, 0.1e-3), 1e-3)
  #
  # Surface temperature (dry, i.e. no fog)
  t_surf  <- theta*(p_surf/p00)**rcp
  #
  # The highest LWP when RH=100% at the surface (no fog)
  rw_max  <- calc_sat_mixr(p_surf, t_surf)
    
  calc_lwp_output <- calc_lwp(p_surf, theta, pblh, rw_max)
  lwp_max <- calc_lwp_output[1]
  zb <- calc_lwp_output[2]
  zc <- calc_lwp_output[3]
  clw_max <- calc_lwp_output[4]
  # No fog cases
  if (lwp_max < lwp){
    if (debug){
      sprintf (fmt = 'Too high LWP (%5.1f g/m2), the maximum is %5.1f g/m2 (theta=%6.2f K, pblh=%3.0f hPa)',
               lwp*1e3, 
               lwp_max*1e3,
               theta,pblh/100.)
    }
    return (-999.)
  }
  #
  # The lowest LWP when RH=0% at the surface
  rw_min  <- 0.
  calc_lwp_output <- calc_lwp(p_surf, theta, pblh, rw_min)
  lwp_min <- calc_lwp_output[1]
  zb <- calc_lwp_output[2]
  zc <- calc_lwp_output[3]
  clw_max <- calc_lwp_output[4]
  if (lwp_min > lwp){
    if (debug){
      sprintf(fmt = 'Too low LWP (%5.1f g/m2), the minimum is %5.1f g/m2 (theta=%6.2f K, pblh=%3.0f hPa)',
              lwp*1e3, 
              lwp_max*1e3,
              theta,pblh/100.)
    return (-999.)
    }
  }
  #
  k  <- 0
  while (k < 100){
    rw_new  <- (rw_min+rw_max)*0.5
    
    calc_lwp_output <- calc_lwp(p_surf, theta, pblh, rw_new)
    lwp_new <- calc_lwp_output[1]
    zb <- calc_lwp_output[2]
    zc <- calc_lwp_output[3]
    clw_max <- calc_lwp_output[4]
    #
    if (abs(lwp-lwp_new) < tol | abs(rw_max-rw_min) < 0.001e-3){
      return (rw_new)}
    else if (lwp < lwp_new){
      rw_max  <- rw_new
    }
    else{
      rw_min  <- rw_new
    }
    k <- k+1
  }
  #
  # Failed
  if (debug){
    sprintf(fmt = 'Iteration failed: current LWP=%5.1f, target LWP=%5.1f',
            lwp_new*1e3,
            lwp*1e3)
  return (-999.)
  }
}