#!/usr/bin/env Rscript
koodihakemisto <- Sys.getenv("KOODIT")
datahakemisto <- Sys.getenv("DATAT")
if (dir.exists("/fmi/projappl/project_2001927/project_rpackages_3.6.3")){
  .libPaths(c("/fmi/projappl/project_2001927/project_rpackages_3.6.3", .libPaths()))
}
source("lib/lib.R")
source("lib/lib_meteo.R")

require("rngWELL")
require("lattice")
require("grid")
library("randtoolbox")
library("lhs")
library("DMwR")
library("hash")

args = commandArgs(trailingOnly=TRUE)

useUpscaling <- FALSE

if (length(args)==0) {
  moodi_nro <- 1
}else{
  moodi_nro <- as.integer(args[1])
}

moodi <- switch(moodi_nro, "test", "SBnight", "SBday", "SALSAnight", "SALSAday")
print(paste("moodi:", moodi))

full_collection <- paste(datahakemisto, "/ECLAIR/eclair_dataset_2001_designvariables.csv", sep="")
sample_collection <- paste(datahakemisto, "/ECLAIR/sample20000.csv", sep="")

if (moodi == "test"){
  filename <- sample_collection
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

use_max_pro <- TRUE

if (use_max_pro){
  measure <- "maxpro"
} else {
  measure <- "maximin"
}

subfolder <- paste("/ECLAIR/design_stats", "_", measure, "/", sep="")


for (key in all_keys){
  look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
  if (file.exists(look_up_table_filename)){
    next
  }
  print("Creating look-up tables")
  if (key == "cos_mu" | key == "rdry_AS_eff"){
    filt_data <- source_data[ source_data$cos_mu > .Machine$double.eps, ]
  } else{
    filt_data <- source_data
  }
  look_up_table <- sort(filt_data[, key])
  look_up_table_filename <- paste(tools::file_path_sans_ext(filename), "_look_up_table_", key, ".csv", sep="")
  write.table(look_up_table,
              file=look_up_table_filename,
              col.names = c(key),
              row.names = FALSE,
              sep=",")
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

if (TRUE){
  print("test look-up table")
  vector_look_up_table(runif(length(design_variables), min = 0, max = 1))
  ma_sobol <- sobol(10, length(design_variables))
  print(matrix_look_up_table(ma_sobol))
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
  

  if( is.nan(c1)){
    print(paste("constraint variables", variables))
  }
  return (c(c1))

}



### sobol
if (FALSE){
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

  design_filename <- paste(datahakemisto, subfolder, moodi, "/", design, "/", design, "_", as.character(design_points), ".csv", sep="")
  dir.create(dirname(design_filename), recursive = TRUE)
  return (design_filename)
}

tau <- c(0,exp(c(1:7)),1e6)

M_scmc <- 300

run_comined <- TRUE



getPoints <- function(design_points){
  print(paste("DESIGN POINTS", design_points))

  if (run_comined){
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
    
    print(" ")

    if (nrow(comined.feasible) > design_points){
      # CoMinED maximin design by one-point-at-a-time greedy algorithm
      print(paste("CoMinED", measure, "design by one-point-at-a-time greedy algorithm"))
      ptm <- proc.time()
      if (useUpscaling) {
        comined.feasible <- matrix_look_up_table(comined.feasible)  
      }
      
      if (! use_max_pro){
        comined.optimised <- maximin.seq(design_points, comined.feasible, return.obj = T)
      } else{
        comined.optimised <- maxpro.seq(design_points, comined.feasible, return.obj = T)
      }

      comined_design <- comined.feasible[comined.optimised$idx,]
      inter_time <- proc.time() - ptm

      print(paste("CoMinED",  measure,  "measure", comined.optimised$obj,
                  "time: ", inter_time[1]))
      comined_time[time_ind] <- inter_time[1]
      comined_obj[time_ind] <- comined.optimised$obj

      write.table(comined_design,
                  file=get_file_name_create_folder("comined", design_points),
                  col.names = design_variables,
                  sep=",")

      print(" ")

    }
  }

  if (run_comined){
    M_scmc <- max(design_points*comined_params_Q, ceiling(comined.all / length(tau)))
  }

  # SCMC candidate points
  if (TRUE){
    best_scmc_obj <- -1
    scmc_design <- NULL
    print("SCMC")
    ptm_all <- proc.time()
    for (kk in scmc_reps){
      print(paste("scmc ", kk, ". run", sep=""))

      use_scaling <- T
      ptm <- proc.time()
      scmc.samp <- scmc(M_scmc, design_dimension, tau, constraint, auto.scale = use_scaling, return.all = T)
      scmc.feasible <- scmc.samp$samp.feasible
      inter_time <- proc.time() - ptm
      print(paste("SCMC: number of feasible samples", nrow(scmc.samp$samp.feasible),
                  "number of total samples", nrow(scmc.samp$samp.all),
                  "autoscaling:", use_scaling,
                  "time: ", inter_time[1]))

      print(" ")


      if (nrow(scmc.feasible) > design_points){
        # SCMC Maximin design
        print(paste("SCMC", measure, "design by one-point-at-a-time greedy algorithm"))
        ptm <- proc.time()
        if (useUpscaling) {
          scmc.feasible <- matrix_look_up_table(scmc.feasible)
        }
        
        if (! use_max_pro){
          scmc.optimised <- maximin.seq(design_points, scmc.feasible, return.obj = T)
          
        } else {
          scmc.optimised <- maxpro.seq(design_points, scmc.feasible, return.obj = T)
        }
        inter_time <- proc.time() - ptm
        print(paste(measure, "measure from SCMC candidate points", scmc.optimised$obj,
                    "time: ", inter_time[1]))
        print(" ")

        if (scmc.optimised$obj > best_scmc_obj){
          scmc_design <- scmc.feasible[scmc.optimised$idx,]
        }


      }

    }

    inter_time <- proc.time() - ptm_all
    scmc_time[time_ind] <- inter_time[1]
    scmc_obj[time_ind] <- scmc.optimised$obj

    write.table(scmc_design,
                file=get_file_name_create_folder("scmc", design_points),
                col.names = design_variables,
                sep=",")
  }

  # LHS
  if (TRUE){
    print("LHS points")
    ptm <- proc.time()
    # set.seed(20211112)
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
    lhs.best <- -1
    if (nrow(lhs.in) > 0){
      if (useUpscaling) {
	      lhs.in <- matrix_look_up_table(lhs.in)
      }
      ptm <- proc.time()
      if (! use_max_pro){
	      lhs_optimised <- maximin.seq(design_points, lhs.in, return.obj = T)
      } else {
	      lhs_optimised <- maxpro.seq(design_points, lhs.in, return.obj = T)
      }
      inter_time <- proc.time() - ptm
      print(paste(measure, "measure from lhs candidate points", lhs_optimised$obj,
                  "time: ", inter_time[1]))
      
	    lhs_design <- lhs.in[lhs_optimised$idx,]
	    write.table(lhs_design,
	              file=get_file_name_create_folder("lhs", design_points),
	              col.names = design_variables,
	              sep=",")
	    lhs.best <- lhs_optimised$obj

    }
    inter_time <- proc.time() - ptm
    lhs_time[time_ind] <- inter_time[1]
    lhs_obj[time_ind] <- lhs.best
  }
}

if (moodi_nro > 1){
  design_points_vector <- c(53, 101, 199, 307, 401, 499)
  scmc_reps <- seq(1)
} else{
  design_points_vector <- c(11)
  scmc_reps <- c(1)
}

comined_time <- rep(-1,length(design_points_vector))
scmc_time <- rep(-1,length(design_points_vector))
lhs_time <- rep(-1,length(design_points_vector))

comined_obj <- rep(-1,length(design_points_vector))
scmc_obj <- rep(-1,length(design_points_vector))
lhs_obj <- rep(-1,length(design_points_vector))

time_ind <- 1
for (p in design_points_vector){
  getPoints(p)
  time_ind <- time_ind + 1
}

stats_df <- data.frame(comined_time, scmc_time, lhs_time,
                       comined_obj, scmc_obj, lhs_obj)
write.table(stats_df,
            file=paste(datahakemisto, subfolder, moodi, "/comined_scmc_lhs_stats.csv", sep=""),
            sep=",")

