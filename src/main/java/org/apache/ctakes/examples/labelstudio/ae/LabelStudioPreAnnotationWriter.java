package org.apache.ctakes.examples.labelstudio.ae;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.uima.UimaContext;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.component.JCasAnnotator_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.jcas.JCas;

import java.util.*;
import java.util.stream.Collectors;

import org.apache.uima.resource.ResourceInitializationException;
import org.healthnlp.annotation.labelstudio.annotation.LabelStudioAnnotation;
import org.healthnlp.annotation.labelstudio.annotation.LabelStudioFileAnnotation;
import org.healthnlp.annotation.labelstudio.result.Result;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static org.healthnlp.annotation.utils.Utils.getJCasFilename;
import static org.healthnlp.annotation.utils.Utils.getTerms;

// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
@PipeBitInfo(
        name = "LabelStudioPreAnnotationWriter",
        description = "Creates a representation of Label Studio for a given note, writes them all to one JSON file at the end.",
        dependencies = { PipeBitInfo.TypeProduct.EVENT }
)
public class LabelStudioPreAnnotationWriter extends JCasAnnotator_ImplBase {
    static private final Logger LOGGER = LoggerFactory.getLogger( "LabelStudioPreAnnotationWriter" );
    private final SortedMap<Integer, LabelStudioFileAnnotation> documentIDtoFileAnnotation = new TreeMap<>();
    private Set<String> IDs = new HashSet<>();
    public static final String PARAM_CTAE_LIST = "ctaeList";

    @ConfigurationParameter(
            name = PARAM_CTAE_LIST,
            description = "Path to the newline separated file of terms to filter out",
            mandatory = false
    )
    private String ctaeList;

    private Set<String> ctaeTerms;
    public static final String PARAM_RT_LIST = "rtList";

    @ConfigurationParameter(
            name = PARAM_RT_LIST,
            description = "Path to the newline separated file of terms to filter out",
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
    public void process(JCas jCas) throws AnalysisEngineProcessException {
        LabelStudioFileAnnotation documentFileAnnotation = new LabelStudioFileAnnotation(
                jCas, this.ctaeTerms, this.rtTerms);
        int documentID = Integer.parseInt(getJCasFilename(jCas).split(",")[0]);
        documentIDtoFileAnnotation.put(documentID, documentFileAnnotation);
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
        ObjectMapper objectMapper = new ObjectMapper();
        int tries = 10;
        super.collectionProcessComplete();
        for (LabelStudioFileAnnotation labelStudioFileAnnotation: documentIDtoFileAnnotation.values()){
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
        }
        try {
            String fullResult = objectMapper.writeValueAsString(
                    documentIDtoFileAnnotation
                            .values()
                            .stream()
                            .sorted()
                            .collect(Collectors.toList())
            );
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
}
