# Write Up:

## Compilation
The following was completed on a Windows 10 machine. To compile this project, first I ran the batch file from my already installed version Visual Studio (14.0) which I found in my Environment Variables:
```
"%VS140COMNTOOLS%vsvars32.bat"
```

Next, I had to suppress a compilation warning for the use of the deprecated <hash_map> in allpairs.h by inserting `#define _SILENCE_STDEXT_HASH_DEPRECATION_WARNINGS` on line 43 of that file.

Compiling and building the program was then executed with the command:
```
nmake -f Makefile.w32
```
Essentially, it was just following the instructions in the README file, but I just substituted the bat file for my installed version of Visual Studio. 

## Executing on Dataset
As the [apriori binary dblp dataset linked on the README](http://www.bayardo.org/bin/dblp_le.bin.gz) leads to a 404 error, I instead opted to use the Orkut dataset mentioned in the paper (pages 6-7). This was because it seemed more accessible than the QSC dataset, which involved finding the five million most popular queries from 2006 and a host of queries, and because it also seemed less complex than the dblp dataset, being comprised of all integers already.
Although I couldn't find the exact full sized dataset that they had mentioned, with 20 million nodes, I was able to find a set online with 3 million nodes on [this webpage](https://snap.stanford.edu/data/com-Orkut.html) all the way at the bottom (specifically [this one](https://snap.stanford.edu/data/bigdata/communities/com-orkut.ungraph.txt.gz)). This dataset was in the format of a txt file, so I wrote a python script to convert it into the aforementioned "apriori binary" dataset format expected for the algorithm. This was more or less just vibe coded by Deepseek, with a little bit of debugging along the way.
To convert the dataset, I then just ran the following:
```
python orkut_to_bin.py    
```

## Modifying Memory Limit
Modifying the memory limit was straightforward as the README already instructs to simply change the parameters for the `FindAllSimilarPairs` function in `allpairs.cc` (with the limit being preset to 1 gb). However, as the Orkut dataset requires a much larger `max_feature_id` than the preset 600,000, I had to consider the memory complexity of the function. From a quick look over at the function, I estimated it to be on the order of `O(max_feature_id + max_features_in_ram)`. Specifically, calculated the memory usage as :
```
max_memory_usage = (sizeof(std::vector<uint32_t>) * max_feature_id_1gb) + (2  *  sizeof(uint32_t) * max_features_in_ram_1gb) + overhead
```
I added some logic in the `main` function to calculate the `max_features_in_ram` and `max_feature_id` as a function of each other with the other values being  constants. The `max_memory_usage` was set to 4294967296, which is the number of bytes in 4gb, and the "overhead" was calculated based on the assumption that the preset values for the two parameters (600,000 and 120,000,000) resulted in using exactly 1gb of memory. As the size of the Orkut dataset was 3072441, this was the value I set for the `max_feature_id` since a node could have any other node in its feature vector. The `max_features_in_ram` would be computed by the compiler, and these two tweaked parameters would then result in modifying the memory usage from 1gb to 4gb. 