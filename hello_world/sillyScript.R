#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

if (length(args)==0) {
  moodi_nro <- 1
}else{
  moodi_nro <- as.integer(args[1])
}

moodi <- switch(moodi_nro, "test", "SBnight", "SBday", "SBnight")
print(paste("moodi:", moodi))
