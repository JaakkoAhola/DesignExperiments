# Add this to your R code:
if dir.exist("/fmi/projappl/project_2001927/project_rpackages_3.6.3"){
    .libPaths(c("/fmi/projappl/project_2001927/project_rpackages_3.6.3", .libPaths()))
    libpath <- .libPaths()[1]

    # This command can be used to check that the folder is now visible:
    .libPaths() # It should be first on the list

    # Package installations should now be directed to the project
    # folder by default. You can also specify the path, e.g. install.packages("package", lib = libpath)

    # Note that it's also possible to fetch the R version automatically using getRversion(). For example:
    .libPaths(paste0("/fmi/projappl/project_2001927/project_rpackages_", gsub("\\.", "", getRversion())))
}
