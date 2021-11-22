source("/home/aholaj/Nextcloud/000_WORK/000_Codex/CoMinED/scripts/lib.R")
source("/home/aholaj/Nextcloud/000_WORK/000_Codex/lhs/lib_meteo.R")
require("rngWELL")
require("lattice")
require("grid")
library("randtoolbox")
library("lhs")
library("DMwR")
library("hash")


moodi <- switch(1, "test", "SBnight", "SBday", "SBnight")

if (moodi == "test"){
  filename <- "/home/aholaj/Data/ECLAIR/sample20000.csv"
  design_points <- 53
  sobol_points <- 100
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc")
  
} else if (moodi == "SBnight"){
  filename <- "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv"
  design_points <- 500
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc")
  
} else if (moodi == "SBday"){
  filename <- "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv"
  design_points <- 500
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "cos_mu")
  
} else if (moodi == "SALSAnight"){
  filename <- "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv"
  design_points <- 135
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff")
  
} else if (moodi == "SALSAday"){
  filename <- "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv"
  design_points <- 150
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff", "cos_mu")
  
}  


all_keys <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "ks", "as", "cs", "rdry_AS_eff", "cos_mu")

print(paste("moodi:", moodi))


source_data_file_name <- filename
source_data <- read.csv(source_data_file_name)

create_lookup_tables <- FALSE

look_up_table_hash <- hash()

if (create_lookup_tables){
  for (key in all_keys){
    look_up_table <- sort(source_data[, key])
    look_up_table_hash[[key]] <- look_up_table
    look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
    write.csv(look_up_table, file=look_up_table_filename, row.names = FALSE)
          # write.csv(sorted_subset)
  }
} else {
  for (key in all_keys){
    look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
    look_up_table_hash[[key]] <- read.csv(look_up_table_filename)
  }
}

func_look_up_table <- function(key, value_within_unit_hyper_cube){
  look_up_table <- look_up_table_hash[[key]]
  samples_in_look_up_table <- length(look_up_table)
  xth_point <- as.integer(round(value_within_unit_hyper_cube * samples_in_look_up_table, 0))
  print(paste(key,xth_point))
  xth_point_of_look_up_table <- max(1, min(xth_point, samples_in_look_up_table)) # index of R starts from 1, and point cant be greater than the number of samples
  
  xth_value <- look_up_table[xth_point_of_look_up_table]
  return (xth_value)
}

#candidate_points_source <- subset(source_data, select = !(names(source_data) %in% c("X")))

candidate_points_source <- subset(source_data, select = (names(source_data) %in% design_variables))

design_dimension <- dim(candidate_points_source)[2]

scaled_candidate_points_source <- scale(candidate_points_source)

constraint <- function(x){
  
  index_keys <- c(1:design_dimension)

  p_surf <- 101780.
  
  
  variables <- hash()
  for (key in all_keys){
    if (key %in% colnames(candidate_points_source)){
      ind <- match(key, colnames(candidate_points_source))
      variables[[key]] <- x[ind]
      index_keys[ind] <- key
    }
  }
  
  variables[["q_pbl"]] <- solve_rw_lwp(p_surf,
               variables[["tpot_pbl"]],
               variables[["lwp"]]*1e-3,
               variables[["pbl"]]*100)*1e3
  c1 <- variables[["q_inv"]] - variables[["q_pbl"]] + 1
  
  # constrain_extreme_values <- TRUE
  # c_min_values <- NULL
  # c_max_values <- NULL
  # if (constrain_extreme_values) {
  #   
  #   c_min_values <- c(1:length(x))
  #   c_max_values <- c(1:length(x))
  #   for (i in 1:length(x)){
  #     
  #     c_min_values[i] <- x[i] - max(candidate_points_source[index_keys[i]])
  #     c_max_values[i] <- min(candidate_points_source[index_keys[i]]) - x[i]
  #   }
  # }
  
  return (c(c1, c_min_values, c_max_values))
  
}

### sobol
if (F){
  print("Getting Sobol points")
  ptm <- proc.time()
  sobol_scaled_samples <- sobol(sobol_points, design_dimension)
  samp <- unscale(sobol_scaled_samples, scaled_candidate_points_source)
  samp.gval <- t(apply(samp, 1, constraint))
  samp.out <- apply(samp.gval, 1, function(x) any(x>0))
  feas.ratio <- 1 - sum(samp.out) / sobol_points
  inter_time <- proc.time() - ptm
  
  print(paste("SOBOL quasi-random: feasibility ratio:", feas.ratio,
              "time: ", inter_time[1] ))
  print(" ")
}

# LHS
if (F){
  ptm <- proc.time()
  set.seed(20211112)
  lhs_scaled <- randomLHS(design_points, design_dimension)
  lhs.all <- unscale(lhs_scaled, scaled_candidate_points_source)
  
  lhs.gval <- t(apply(lhs.all, 1, constraint))
  
  lhs.out.idx <- apply(lhs.gval, 1, function(x) return(any(x>0)))
  lhs.out <- lhs.all[lhs.out.idx,]
  lhs.in <- lhs.all[!lhs.out.idx,]
  inter_time <- proc.time() - ptm
  print(paste("LHS: number of feasible samples", nrow(lhs.in),
              "total samples", nrow(lhs.all),
              "time: ", inter_time[1]))
  print(" ")
}

tau <- c(0,exp(c(1:7)),1e6)

# SCMC candidate points
if (F){
  ptm <- proc.time()
  use_scaling <- T
  scmc.samp <- scmc(10, design_dimension, tau, constraint, auto.scale = use_scaling, return.all = T, scaled_candidate_points_source)
  scmc.feasible <- scmc.samp$samp.feasible
  inter_time <- proc.time() - ptm
  print(paste("SCMC: number of feasible samples", nrow(scmc.samp$samp.feasible),
            "number of total samples", nrow(scmc.samp$samp.all),
            "autoscaling:", use_scaling,
            "time: ", inter_time[1]))
  print(" ")

  # SCMC Maximin design
  print("SCMC maximin design by one-point-at-a-time greedy algorithm")
  ptm <- proc.time()
  scmc.maximin <- maximin.seq(design_points, scmc.feasible, return.obj = T)
  inter_time <- proc.time() - ptm
  print(paste("Maximin measure from SCMC candidate points", scmc.maximin$obj,
              "time: ", inter_time[1]))
  print(" ")
  
  
  # SCMC MAXPRO
  print("SCMC maxpro design by one-point-at-a-time greedy algorithm")
  ptm <- proc.time()
  scmc.maxpro <- maxpro.seq(design_points, scmc.feasible, return.obj = T)
  inter_time <- proc.time() - ptm
  print(paste("Maxpro measure from SCMC candidate points", scmc.maximin$obj,
              "time: ", inter_time[1]))
  print(" ")
}

if (TRUE){
  # Constrained Minimum Energy Design
  print("Constrained Minimum Energy Design")
  ptm <- proc.time()
  comined.output <- comined(n = design_points, p = design_dimension, tau = tau, constraint = constraint,
                            n.aug = 17, auto.scale = F, s = 2)
  
  comined.all <- comined.output$cand
  comined.feasible <- comined.output$cand[comined.output$feasible.idx,]
  inter_time <- proc.time() - ptm
  print(paste("CoMinED",
              "Number of total samples", nrow(comined.all),
              "number of feasible samples", nrow(comined.feasible),
              "time: ", inter_time[1]))
              
  print(" ")
  
  # CoMinED maximin design by one-point-at-a-time greedy algorithm
  print("CoMinED maximin design by one-point-at-a-time greedy algorithm")
  ptm <- proc.time()
  comined.maximin <- maximin.seq(design_points, comined.feasible, return.obj = T)
  inter_time <- proc.time() - ptm
  
  print(paste("CoMinED maximin measure", comined.maximin$obj,
              "time: ", inter_time[1]))
              
  print(" ")
  
  # CoMinED maxpro design by one-point-at-a-time greedy algorithm
  print("CoMinED maxpro design by one-point-at-a-time greedy algorithm")
  ptm <- proc.time()
  comined.maxpro <- maxpro.seq(design_points, comined.feasible, return.obj = T)
  inter_time <- proc.time() - ptm
  print(paste("CoMinED maxpro measure", comined.maxpro$obj,
              "time: ", inter_time[1]))
  
  print(" ")
  # CoMinED
  print("Constrained Minimum Energy Design AUTOSCALED")
  ptm <- proc.time()
  comined.output <- comined(n = design_points, p = design_dimension, tau = tau, constraint = constraint,
                            n.aug = 5, auto.scale = T, s = 2)
  comined.all <- comined.output$cand
  comined.feasible <- comined.output$cand[comined.output$feasible.idx,]
  inter_time <- proc.time() - ptm
  print(paste("CoMinED autoscaled: number of total samples", nrow(comined.all),
              "number of feasible samples", nrow(comined.feasible),
              "time: ", inter_time[1]))
}

# # Source maximin design by one-point-at-a-time greedy algorithm
# print("Source maximin design by one-point-at-a-time greedy algorithm")
# ptm <- proc.time()
# source.maximin <- maximin.seq(design_points, candidate_points_source, return.obj = T)
# inter_time <- proc.time() - ptm
# 
# print(paste("Source maximin measure", comined.maximin$obj,
#             "time: ", inter_time[1]))
# 
# print(" ")
# 
# # Source maxpro design by one-point-at-a-time greedy algorithm
# print("Source maxpro design by one-point-at-a-time greedy algorithm")
# ptm <- proc.time()
# comined.maxpro <- maxpro.seq(design_points, candidate_points_source, return.obj = T)
# inter_time <- proc.time() - ptm
# print(paste("Source maxpro measure", comined.maxpro$obj,
#             "time: ", inter_time[1]))

# BSP maximin & maxpro measure???
