# Quick phase matching algorithm

Based on the histogram binning. Uses 3 tables `backend_ref*` defined in `schema/schema.sql`.

The basic idea is to have the experimental reflections (peaks) identified and compared to the reference data. To do this a background function is added to enable background subtraction. This is very helpful when doing a peak search and intensity estimation. The code can be used to do a search by using either a directory of dI files, or Postgres tables, as a reference database. The search and match is implemented as a computation of figures of merit (FoM) between the experimental data given and each of the reference data available. The best FoM should coincide with the most likely candidate.

Original idea by Bernd Hinrichsen @HinrichsenB and Sigurdur Smarason @SiggiSmara


## License

Copyright 2021-2023 BASF SE

BSD 3-Clause
