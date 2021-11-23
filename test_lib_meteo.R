setwd("/home/aholaj/Nextcloud/000_WORK/000_Codex/lhs")
source("lib_meteo.R")

ab <- solve_rw_lwp(101780,
             285.28396602292037,
             315.58040763791155*1e-3,
             260.867076637996*100.)
print(paste(0.0037222520919583764, ab))
bb <- solve_rw_lwp(101780., 293., 100e-3, 20000.)

print(paste(0.00723684088331, bb))