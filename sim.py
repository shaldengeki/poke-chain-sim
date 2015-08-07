#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import math
import random

def shiny_probability_binomial(chain_length):
  # returns a flat probability of shiny.
  return 1.0/308

def shiny_probability_dependent(chain_length):
  # returns probability of shiny, dependent on chain length
  if chain_length >= 40:
    return 0.05
  return float(14747 - 40 * chain_length) / (2621440 * (41 - chain_length))

def is_shiny(chain_length, probability_function):
  return random.random() < probability_function(chain_length)

def chain_until_shiny(probability_function):
  chain_length = 0
  while True:
    chain_length += 1
    if is_shiny(chain_length, probability_function):
      return chain_length

def chain_distribution(n, probability_function):
  lengths = []
  for _ in xrange(n):
    lengths.append(chain_until_shiny(probability_function))
  return collections.Counter(lengths)

def dist_percentages(dist):
  # convert a dist of raw counts to frequencies.
  dist_sum = float(sum(dist[k] for k in dist))
  for k in dist:
    dist[k] = dist[k] / dist_sum
  return dist

def fill_dist_keys(dist1, dist2):
  # fills dist1 and dist2 with zero for any keys that exist in the other distribution.
  for k in dist1:
    if k not in dist2:
      dist2[k] = 0
  for k in dist2:
    if k not in dist1:
      dist1[k] = 0
  return dist1,dist2

def dist_rmse(dist1, dist2):
  # root mean squared error of dist1, taking dist2 as a baseline.
  # assumes dist1 and dist2 are filled to have the same keys.
  return pow(sum(pow(dist1[k] - dist2[k], 2) for k in dist1) / float(len(dist1)), 0.5)

def output_chain_dist(dists, filename):
  with open(filename, 'w') as dist_file:
    max_key = max(max(dist.keys()) for dist in dists)
    for k in xrange(1, max_key+1):
      dist_file.write(','.join([str(k)] + [str(dist[k]) if k in dist else '0' for dist in dists]) + '\n')

def bin_dist(dist, bin_length):
  # bins a distribution into bin_length-length bins.
  new_dist = collections.Counter()
  for k,v in dist.iteritems():
    new_dist[(int(math.ceil(k / bin_length) + 1) * bin_length)] += v
  return new_dist

def binned_sample_dist(n, probability_function, bin_size):
  return dist_percentages(bin_dist(chain_distribution(n, probability_function), bin_size))

def dist_cdf(dist):
  cum_sum = 0
  for k in sorted(dist.keys()):
    this_sum = cum_sum + dist[k]
    cum_sum = this_sum
    dist[k] = this_sum
  return dist

def sample_dist_rmse(sample_dist, null_dist):
  sample_dist, null_dist = fill_dist_keys(sample_dist, null_dist)
  return dist_rmse(sample_dist, null_dist)

def kolmogorov_two_sample(dist1, dist1_n, dist2, dist2_n, c_alpha):
  max_stat = max(abs(dist1[k] - dist2[k]) for k in dist1)
  return max_stat > c_alpha * pow(float(dist1_n + dist2_n) / (dist1_n * dist2_n), 0.5)

def count_sample_dists_worse_than(num_dists, dist_size, test_err, null_dist, probability_function, bin_size):
  higher_error_count = 0
  for _ in xrange(num_dists):
    if sample_dist_rmse(binned_sample_dist(dist_size, probability_function, bin_size), null_dist) >= test_err:
      higher_error_count += 1
  return higher_error_count

# reddit data, binned into 20s.
test_dist = collections.Counter({
  20: 6,
  40: 6,
  60: 13,
  80: 8,
  100: 10,
  120: 8,
  140: 4,
  160: 4,
  180: 2,
  200: 1,
  220: 4,
  240: 0,
  260: 1,
  280: 0,
  300: 1,
  320: 1
})
test_shinies = sum(test_dist[k] for k in test_dist)

test_dist = dist_percentages(test_dist)

# null hypothesis, that shiny encounter rate is dependent on chain length
null_dist_size = 10000
null_dist = chain_distribution(null_dist_size, shiny_probability_dependent)

# bin null hypothesis into 20-length bins and convert to percentages.
null_dist = dist_percentages(bin_dist(null_dist, 20))

# fill test_dist and null_dist with 0-keys.
test_dist,null_dist = fill_dist_keys(test_dist, null_dist)

# "error" between our experimental data and the null hypothesis.
test_err = dist_rmse(test_dist, null_dist)

# generate sample distributions of length test_shinies and see what % have an error rate at least that of our experimental data.
print str(count_sample_dists_worse_than(10000, test_shinies, test_err, null_dist, shiny_probability_dependent, 20)) + " out of 1000 distributions were further off the null hypothesis than our experimental data."

# run kolmogorov two-sample test at alpha = .001
print "Kolmogorov two sample test: should we reject null hypothesis?"
print kolmogorov_two_sample(null_dist, null_dist_size, test_dist, test_shinies, 1.95)