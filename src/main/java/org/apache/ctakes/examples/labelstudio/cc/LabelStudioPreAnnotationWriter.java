package org.apache.ctakes.examples.labelstudio.cc;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ctakes.core.cc.AbstractJCasFileWriter;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.uima.jcas.JCas;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.*;
import java.util.stream.Collectors;

import org.healthnlp.annotation.labelstudio.annotation.LabelStudioAnnotation;
import org.healthnlp.annotation.labelstudio.annotation.LabelStudioFileAnnotation;
import org.healthnlp.annotation.labelstudio.result.Result;

import static org.healthnlp.annotation.utils.Utils.getSaltString;

// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
@PipeBitInfo(
        name = "LabelStudioPreAnnotationWriter",
        description = "Creates a representation of Label Studio for a given note, writes them all to one JSON file at the end.",
        role = PipeBitInfo.Role.WRITER
)
final public class LabelStudioPreAnnotationWriter extends AbstractJCasFileWriter {
    private final Set<String> IDs = new HashSet<>();
    private final ObjectMapper JSONSerializer = new ObjectMapper();

    @Override
    public void writeFile(JCas data, String outputDir, String documentId, String fileName) throws IOException {
        LabelStudioFileAnnotation labelStudioFileAnnotation = new LabelStudioFileAnnotation(data);
        int tries = 10;
        for (LabelStudioAnnotation labelStudioAnnotation: labelStudioFileAnnotation.predictions){
            Collection<List<Result>> resultClusters = labelStudioAnnotation
                    .result
                    .stream()
                    .collect(Collectors.groupingBy(r -> List.of(r.value.start, r.value.end)))
                    .values();
            for (List<Result> results: resultClusters){
                for (int i = 0; i < tries; i++) {
                    String attemptedId = getSaltString();
                    if (!IDs.contains(attemptedId)){
                        for (Result result: results) {
                            result.setId(attemptedId);
                        }
                        IDs.add(attemptedId);
                        // there's probably a better way but for now
                        break;
                    }
                }
            }
        }
        try {
            String fullResult = this.JSONSerializer.writeValueAsString(labelStudioFileAnnotation);
            Files.write(Paths.get(outputDir, String.format("%s.json", documentId)),
                    List.of(fullResult ), StandardCharsets.UTF_8, StandardOpenOption.CREATE);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
}
