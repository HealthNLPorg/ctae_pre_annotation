package org.apache.ctakes.examples.labelstudio.cc;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.lang3.StringUtils;
import org.apache.ctakes.core.cc.AbstractJCasFileWriter;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.uima.UimaContext;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.jcas.JCas;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.*;
import java.util.stream.Collectors;

import org.apache.uima.resource.ResourceInitializationException;
import org.healthnlp.annotation.labelstudio.annotation.LabelStudioAnnotation;
import org.healthnlp.annotation.labelstudio.annotation.LabelStudioFileAnnotation;
import org.healthnlp.annotation.labelstudio.result.Result;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static org.healthnlp.annotation.utils.Utils.getTerms;

// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
@PipeBitInfo(
        name = "LabelStudioPreAnnotationWriter",
        description = "Creates a representation of Label Studio for a given note, writes them all to one JSON file at the end.",
        dependencies = { PipeBitInfo.TypeProduct.EVENT }
)
public class LabelStudioPreAnnotationWriter extends AbstractJCasFileWriter {
    static private final Logger LOGGER = LoggerFactory.getLogger( "LabelStudioPreAnnotationWriter" );
    private final SortedMap<Integer, LabelStudioFileAnnotation> documentIDtoFileAnnotation = new TreeMap<>();
    private final Set<String> IDs = new HashSet<>();
    private ObjectMapper JSONSerializer = new ObjectMapper();
    public static final String PARAM_CTAE_LIST = "ctaeList";

    @ConfigurationParameter(
            name = PARAM_CTAE_LIST,
            description = "Path to the newline separated file of CTAE CUIs"
    )
    private String ctaeList;

    public static final String PARAM_OUTPUT_JSON = "outputJSON";

    @ConfigurationParameter(
            name = PARAM_OUTPUT_JSON,
            description = "Path to output JSON file"
    )
    private String outputJSON;
    private String outputDir;

    private Set<String> ctaeTerms;
    public static final String PARAM_RT_LIST = "rtList";

    @ConfigurationParameter(
            name = PARAM_RT_LIST,
            description = "Path to the newline separated file of radiotherapy treatment CUIs",
            mandatory = false
    )
    private String rtList;

    private Set<String> rtTerms;
    @Override
    public void initialize( UimaContext context ) throws ResourceInitializationException {
        super.initialize( context );
        this.ctaeTerms = getTerms(this.ctaeList);
        this.rtTerms = getTerms(this.rtList);
    }

    @Override
    public void writeFile(JCas data, String outputDir, String documentId, String fileName) throws IOException {
        LabelStudioFileAnnotation labelStudioFileAnnotation = new LabelStudioFileAnnotation(
                data, this.ctaeTerms, this.rtTerms);
        int tries = 10;
        for (LabelStudioAnnotation labelStudioAnnotation: labelStudioFileAnnotation.annotations){
            for (Result result: labelStudioAnnotation.result){
                for (int i = 0; i < tries; i++) {
                    String attemptedId = getSaltString();
                    if (!IDs.contains(attemptedId)){
                        result.setId(attemptedId);
                        IDs.add(attemptedId);
                        // there's probably a better way but for now
                        break;
                    }
                }
            }
        }
        this.outputDir = outputDir;
        try {
            String fullResult = this.JSONSerializer.writeValueAsString(labelStudioFileAnnotation);
            Files.write(Paths.get(outputDir, this.outputJSON),
                    List.of(fullResult + ","), StandardCharsets.UTF_8, StandardOpenOption.APPEND);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }


    protected String getSaltString() {
        String SALTCHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_";
        StringBuilder salt = new StringBuilder();
        Random rnd = new Random();
        while (salt.length() < 10) { // length of the random string.
            int index = (int) (rnd.nextFloat() * SALTCHARS.length());
            salt.append(SALTCHARS.charAt(index));
        }
        return salt.toString();
    }

    @Override
    public void collectionProcessComplete() throws AnalysisEngineProcessException {
        super.collectionProcessComplete();
        try {
            String rawText = new BufferedReader(
                    new InputStreamReader(
                            new FileInputStream(
                                    Paths.get(this.outputDir, this.outputJSON).toFile()
                            ),
                            StandardCharsets.UTF_8))
                    .lines()
                    .collect(Collectors.joining("\n"));
            String updatedText =
                    String.format(
                            "[%s]", StringUtils.stripEnd(rawText, ",")
                    );
            Files.write(Paths.get(this.outputDir, this.outputJSON),
                    List.of(updatedText), StandardCharsets.UTF_8, StandardOpenOption.WRITE);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
