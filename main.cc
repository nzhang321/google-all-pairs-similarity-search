// Copyright 2007 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// ---
// A simple all-similar-pairs algorithm for binary vector input.
// ---
// Author: Roberto Bayardo

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include <iostream>
#include <memory>

#include "allpairs.h"
#include "data-source-iterator.h"

int main(int argc, char** argv) {
  time_t start_time;
  time(&start_time);

  const long max_memory_usage = 4294967296;
  const long max_feature_id_1gb = 600000; // previously set max feature id, size for a single vector
  const long max_features_in_ram_1gb = 120000000; // previously set max features in ram for 1 gb
  const long overhead = (max_memory_usage / 4) - (sizeof(std::vector<uint32_t>) * max_feature_id_1gb) - (2 * sizeof(uint32_t) * max_features_in_ram_1gb) ;// computing the previously unallocated overhead within the 1 gb limit
  const long max_feature_id_4gb = 3072241; // size of the new dataset
  const long max_features_in_ram_4gb = (max_memory_usage - (sizeof(std::vector<uint32_t>) * max_feature_id_4gb) - (overhead * 4)) / (2 * sizeof(uint32_t)); // computing how much max_features_in_ram can be set for 4gb

  // Verify input arguments.
  if (argc != 3) {
    std::cerr << "ERROR: Usage is: ./ap <sim_threshold> <dataset_path>\n";
    return 1;
  }
  const double threshold = strtod(argv[1], 0);
  if (threshold <= 0.0 || threshold > 1.0) {
    std::cerr << "ERROR: The first argument should be a similarity "
              << "threshhold with range (0.0-1.0]\n";
    return 2;
  }
  std::cerr << "; User specified similarity threshold: "
            << threshold << std::endl;

  {
    std::auto_ptr<DataSourceIterator> data(DataSourceIterator::Get(argv[2]));
    if (!data.get())
      return 3;
    AllPairs ap;
    bool result =
        ap.FindAllSimilarPairs(threshold, data.get(), max_feature_id_4gb, max_features_in_ram_4gb);
    if (!result) {
      std::cerr << "ERROR: " << data->GetErrorMessage() << "\n";
      return 4;
    }
    std::cerr << "; Found " << ap.SimilarPairsCount() << " similar pairs.\n"
              << "; Candidates considered: " << ap.CandidatesConsidered()
              << "\n"
              << "; Vector intersections performed: "
              << ap.IntersectionsPerformed() << '\n';
  }

  time_t end_time;
  time(&end_time);
  std::cerr << "; Total running time: " << (end_time - start_time)
            << " seconds" << std::endl;

  return 0;
}
