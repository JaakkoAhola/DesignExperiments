#!/usr/bin/env Rscript
koodihakemisto <- Sys.getenv("KOODIT")
datahakemisto <- Sys.getenv("DATAT")
if (dir.exists("/fmi/projappl/project_2001927/project_rpackages_3.6.3")){
  .libPaths(c("/fmi/projappl/project_2001927/project_rpackages_3.6.3", .libPaths()))
}
source(paste(koodihakemisto, "/CoMinED/scripts/lib.R", sep=""))
source(paste(koodihakemisto, "/DesignExperiments/lib_meteo.R", sep=""))
source(paste(koodihakemisto, "/DesignExperiments/puhti_env.R", sep=""))
require("rngWELL")
require("lattice")
require("grid")
library("randtoolbox")
library("lhs")
library("DMwR")
library("hash")

args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  moodi_nro <- 1
}else{
  moodi_nro <- as.integer(args[1])
}

moodi <- switch(moodi_nro, "test", "SBnight", "SBday", "SBnight")
print(paste("moodi:", moodi))

full_collection <- paste(datahakemisto, "/ECLAIR/eclair_dataset_2001_designvariables.csv", sep="")

if (moodi == "test"){
  filename <- paste(datahakemisto, "/ECLAIR/sample20000.csv", sep="")
  design_points <- 100
  sobol_points <- 200
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc")
  comined_params_Q <- 5
  
} else if (moodi == "SBnight"){
  filename <- full_collection
  design_points <- 500
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc")
  comined_params_Q <- 19
  
} else if (moodi == "SBday"){
  filename <- full_collection
  design_points <- 500
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "cos_mu")
  comined_params_Q <- 19
  
} else if (moodi == "SALSAnight"){
  filename <- full_collection
  design_points <- 135
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff")
  comined_params_Q <- 23
  
} else if (moodi == "SALSAday"){
  filename <- full_collection
  design_points <- 150
  sobol_points <- 1e4
  design_variables <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff", "cos_mu")
  comined_params_Q <- 23
  
}

all_keys <- c("q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "ks", "as", "cs", "rdry_AS_eff", "cos_mu")

source_data_file_name <- filename
source_data <- read.csv(source_data_file_name)



look_up_table_hash <- hash()

use_max_pro <- FALSE


for (key in all_keys){
  look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
  if (file.exists(look_up_table_filename)){
    next
  }
  print("Creating look-up tables")
  if (key == "cos_mu"){
    filt_data <- source_data[ source_data$cos_mu > .Machine$double.eps, ]
  } else{
    filt_data <- source_data 
  }
  look_up_table <- sort(filt_data[, key])
  look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
  write.csv(look_up_table, file=look_up_table_filename, row.names = FALSE)
        # write.csv(sorted_subset)
}


for (key in design_variables){
    look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
    look_up_table_hash[[key]] <- read.csv(look_up_table_filename)
}


func_look_up_table <- function(key, value_within_unit_hyper_cube){
  
  look_up_table <- look_up_table_hash[[key]]
  samples_in_look_up_table <- dim(look_up_table)[1]
  xth_point <- as.integer(round(value_within_unit_hyper_cube * samples_in_look_up_table, 0))
  xth_point_of_look_up_table <- max(1, min(xth_point, samples_in_look_up_table)) # index of R starts from 1, and point cant be greater than the number of samples
  
  xth_value <- look_up_table[xth_point_of_look_up_table,]
  return (xth_value)
}

vector_look_up_table <- function(vec){
  scaled_vector <- numeric(length(vec))
  i <- 1
  for (key in design_variables){
    scaled_vector[i] <- func_look_up_table(key, vec[i])
    i <- i + 1
  }
  return(scaled_vector)
}

matrix_look_up_table <- function(ma){
  scaled_matrix <- matrix(, nrow = nrow(ma), ncol =ncol(ma))
  
  for(row in 1:nrow(ma)){
    scaled_matrix[row,] <- vector_look_up_table(ma[row,])
  }
  return (scaled_matrix)
}

if (FALSE){
  print("test look-up table")
  vector_look_up_table(runif(length(design_variables), min = 0, max = 1))
  ma_sobol <- sobol(10, length(design_variables))
  matrix_look_up_table(ma_sobol)
}

#candidate_points_source <- subset(source_data, select = !(names(source_data) %in% c("X")))

candidate_points_source <- subset(source_data, select = (names(source_data) %in% design_variables))

design_dimension <- dim(candidate_points_source)[2]

# scaled_candidate_points_source <- scale(candidate_points_source)

constraint <- function(x){
  
  index_keys <- c(1:design_dimension)

  p_surf <- 101780.
  
  
  variables <- hash()
  for (key in design_variables){
      ind <- match(key, design_variables)
      variables[[key]] <- func_look_up_table(key, x[ind])
      index_keys[ind] <- key
    
  }
  
  variables[["q_pbl"]] <- solve_rw_lwp(p_surf,
               variables[["tpot_pbl"]],
               variables[["lwp"]]*1e-3,
               variables[["pbl"]]*100)*1e3
  c1 <- variables[["q_inv"]] - variables[["q_pbl"]] + 1
  
  constrain_extreme_values <- FALSE
  c_min_values <- NULL
  c_max_values <- NULL
  if (constrain_extreme_values) {

    c_min_values <- c(1:length(x))
    c_max_values <- c(1:length(x))
    for (i in 1:length(x)){

      c_min_values[i] <- x[i] - max(candidate_points_source[index_keys[i]])
      c_max_values[i] <- min(candidate_points_source[index_keys[i]]) - x[i]
    }
  }
  
  return (c(c1, c_min_values, c_max_values))
  
}



### sobol
if (TRUE){
  print("Getting Sobol points")
  ptm <- proc.time()
  samp <- sobol(sobol_points, design_dimension)
  samp.gval <- t(apply(samp, 1, constraint))
  samp.out <- apply(samp.gval, 1, function(x) any(x>0))
  feas.ratio <- 1 - sum(samp.out) / sobol_points
  inter_time <- proc.time() - ptm
  
  print(paste("SOBOL quasi-random: feasibility ratio:", feas.ratio,
              "time: ", inter_time[1] ))
  print(" ")
}


get_file_name_create_folder <- function(design, design_points){
  
  design_filename <- paste(datahakemisto, "/ECLAIR/design_stats/", moodi, "/", design, "_", as.character(design_points), ".csv", sep="")
  dir.create(dirname(design_filename))
  return (design_filename)
}

tau <- c(0,exp(c(1:7)),1e6)




getPoints <- function(design_points){
  print(paste("DESIGN POINTS", design_points))
  if (TRUE){
    # Constrained Minimum Energy Design
    print("Constrained Minimum Energy Design")
    ptm <- proc.time()
    comined.output <- comined(n = design_points, p = design_dimension, tau = tau, constraint = constraint,
                              n.aug = comined_params_Q, auto.scale = T, s = 2)
    
    comined.all <- comined.output$cand
    comined.feasible <- comined.output$cand[comined.output$feasible.idx,]
    inter_time <- proc.time() - ptm
    print(paste("CoMinED",
                "Number of total samples", nrow(comined.all),
                "number of feasible samples", nrow(comined.feasible),
                "time: ", inter_time[1]))
    
    scaled_up_comined_feasible <- matrix_look_up_table(comined.feasible)
    write.csv(scaled_up_comined_feasible, file=get_file_name_create_folder("comined", design_points))
    print(" ")
    
    # CoMinED maximin design by one-point-at-a-time greedy algorithm
    print("CoMinED maximin design by one-point-at-a-time greedy algorithm")
    ptm <- proc.time()
    comined.maximin <- maximin.seq(design_points, comined.feasible, return.obj = T)
    inter_time <- proc.time() - ptm
    
    print(paste("CoMinED maximin measure", comined.maximin$obj,
                "time: ", inter_time[1]))
                
    print(" ")
    
    # Upscaled CoMinED maximin design by one-point-at-a-time greedy algorithm
    print("Upscaled CoMinED maximin design by one-point-at-a-time greedy algorithm")
    ptm <- proc.time()
    comined.maximin <- maximin.seq(design_points, scaled_up_comined_feasible, return.obj = T)
    inter_time <- proc.time() - ptm
    
    print(paste("CoMinED maximin measure", comined.maximin$obj,
                "time: ", inter_time[1]))
    
    print(" ")
    
    if (use_max_pro){
    # CoMinED maxpro design by one-point-at-a-time greedy algorithm
    print("CoMinED maxpro design by one-point-at-a-time greedy algorithm")
    ptm <- proc.time()
    comined.maxpro <- maxpro.seq(design_points, comined.feasible, return.obj = T)
    inter_time <- proc.time() - ptm
    print(paste("CoMinED maxpro measure", comined.maxpro$obj,
                "time: ", inter_time[1]))
    }
  }  
  
  M_scmc <- max(design_points*comined_params_Q, ceiling(comined.all / length(tau)))
  
  # SCMC candidate points
  if (TRUE){
    ptm <- proc.time()
    use_scaling <- T
    
    scmc.samp <- scmc(M_scmc, design_dimension, tau, constraint, auto.scale = use_scaling, return.all = T)
    scmc.feasible <- scmc.samp$samp.feasible
    inter_time <- proc.time() - ptm
    print(paste("SCMC: number of feasible samples", nrow(scmc.samp$samp.feasible),
                "number of total samples", nrow(scmc.samp$samp.all),
                "autoscaling:", use_scaling,
                "time: ", inter_time[1]))
    scaled_up_scmc_feasible <- matrix_look_up_table(scmc.feasible)
    write.csv(scaled_up_scmc_feasible, file=get_file_name_create_folder("scmc", design_points))
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
    if (use_max_pro){
      print("SCMC maxpro design by one-point-at-a-time greedy algorithm")
      ptm <- proc.time()
      scmc.maxpro <- maxpro.seq(design_points, scmc.feasible, return.obj = T)
      inter_time <- proc.time() - ptm
      print(paste("Maxpro measure from SCMC candidate points", scmc.maximin$obj,
                  "time: ", inter_time[1]))
      print(" ")
    }
  }
  
  # LHS
  if (TRUE){
    print("LHS points")
    ptm <- proc.time()
    set.seed(20211112)
    lhs <- randomLHS(M_scmc, design_dimension)
    lhs.gval <- t(apply(lhs, 1, constraint))
    lhs.out.idx <- apply(lhs.gval, 1, function(x) return(any(x>0)))
    lhs.out <- lhs[lhs.out.idx,]
    lhs.in <- lhs[!lhs.out.idx,]
    inter_time <- proc.time() - ptm
    print(paste("LHS: number of feasible samples", nrow(lhs.in),
                "total samples", nrow(lhs),
                "time: ", inter_time[1]))
    print(" ")
    scaled_up_lhs.in_feasible <- matrix_look_up_table(lhs.in)
    write.csv(lhs.in, file=get_file_name_create_folder("lhs", design_points))
  }
}

if (moodi_nro > 1){
  for (p in seq(100,110,10)){
    getPoints(p)
  }
} else{
  getPoints(100)
}

  # print(" ")
  # # CoMinED
  # print("Constrained Minimum Energy Design AUTOSCALED")
  # ptm <- proc.time()
  # comined.output <- comined(n = design_points, p = design_dimension, tau = tau, constraint = constraint,
  #                           n.aug = 5, auto.scale = T, s = 2)
  # comined.all <- comined.output$cand
  # comined.feasible <- comined.output$cand[comined.output$feasible.idx,]
  # inter_time <- proc.time() - ptm
  # print(paste("CoMinED autoscaled: number of total samples", nrow(comined.all),
  #             "number of feasible samples", nrow(comined.feasible),
  #             "time: ", inter_time[1]))



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
