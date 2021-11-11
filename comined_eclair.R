#source("../CoMinED/scripts/lib.R")
source("lib_meteo.R")
library("randtoolbox")
require("rngWELL")

source_data_file_name <- "/home/aholaj/Data/ECLAIR/sample20000.csv"
source_data <- read.csv(source_data_file_name)



constraint <- function(x){
  
  index_keys <- c(1:11)

  p_surf <- 101780.
  
  q_inv <- x[1]
  index_keys[1] <- "q_inv"
  
  tpot_inv <- x[2]
  index_keys[2] <- "tpot_inv"
  
  lwp <- x[3]
  index_keys[3] <- "lwp"
  
  tpot_pbl <- x[4]
  index_keys[4] <- "tpot_pbl"
  
  pbl <- x[5]
  index_keys[5] <- "pbl"
  
  cdnc <- x[6]
  index_keys[6] <- "cdnc"
  
  ks <- x[7]
  index_keys[7] <- "ks"
  
  as <- x[8]
  index_keys[8] <- "as"
  
  cs <- x[9]
  index_keys[9] <- "cs"
  
  rdry_AS_eff <-x[10]
  index_keys[10] <- "rdry_AS_eff"
  
  cos_mu <- x[11]
  index_keys[11] <- "cos_mu"
  
  
  q_pbl <- solve_rw_lwp(p_surf,
               tpot_pbl,
               lwp*1e-3,
               pbl*100)*1e3
  c1 <- q_inv - q_pbl + 1
  
  
  constrain_extreme_values <- TRUE
  c_min_values <- NULL
  c_max_values <- NULL
  if (constrain_extreme_values) {
    
    c_min_values <- c(1:length(x))
    c_max_values <- c(1:length(x))
    for (i in 1:length(x)){
      
      c_min_values[i] <- x[i] - max(source_data[index_keys[i]])
      c_max_values[i] <- min(source_data[index_keys[i]]) - x[i]
    }
  }
  
  return (c(c1, c_min_values, c_max_values))
  
}