To compile this project, first I ran the batch file from my already installed version Visual Studio (14.0) which I found in my Environment Variables
```
"%VS140COMNTOOLS%vsvars32.bat"
```
Next, I had to suppress a compilation warning for the use of the deprecated <hash_map> in allpairs.h by inserting 
```
#define _SILENCE_STDEXT_HASH_DEPRECATION_WARNINGS
```
on line 43 of that file. 
Compiling and building the program was then executed with the command
```
nmake -f Makefile.w32
```

As the dataset linked on the README "http://www.bayardo.org/bin/dblp_le.bin.gz" leads to a 404 error, I instead opted to use the orkut dataset mentioned in the paper. Although I couldn't find the exact full sized dataset that they had mentioned, with 20 million nodes, I was able to find one online with 3 million nodes on this webpage at the bottom [https://snap.stanford.edu/data/com-Orkut.html]. This dataset was a txt file, so I wrote a python script to convert it into the aforementioned "apriori binary" dataset format expected for the algorithm.