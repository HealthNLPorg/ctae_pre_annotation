#!/bin/bash -i
java -cp ./target/ctae-pre-annotation-6.0.0-jar-with-dependencies.jar  \
     org.apache.ctakes.core.pipeline.PiperFileRunner \
     -p org/apache/ctakes/examples/labelstudio/pipeline/DictionaryDTRLabelStudio \
     -i ~/Documents/ctae_note_tests/input/ \
     -o ~/Documents/ctae_note_tests/output/ \
     -l org/apache/ctakes/dictionary/lookup/fast/bsv/RTAndCTAE.xml \

