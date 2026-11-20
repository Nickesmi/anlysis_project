# CMP3005 plagiarism detector
#   make          builds ./plagiarism
#   make test     builds and runs the self-test
CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra

SOURCES = src/main.cpp src/text_processing.cpp src/similarity.cpp \
          src/brute_force.cpp src/efficient.cpp src/output.cpp src/benchmark.cpp
LIBRARY = $(filter-out src/main.cpp,$(SOURCES))

plagiarism: $(SOURCES) src/plagiarism.h
	$(CXX) $(CXXFLAGS) -o $@ $(SOURCES)

selftest: tests/selftest.cpp $(LIBRARY) src/plagiarism.h
	$(CXX) $(CXXFLAGS) -Isrc -o $@ tests/selftest.cpp $(LIBRARY)

test: selftest
	./selftest

clean:
	rm -f plagiarism selftest

.PHONY: test clean
