package org.apache.ctakes.examples.labelstudio.ae;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.io.FilenameUtils;
import org.apache.ctakes.core.cc.AbstractJCasFileWriter;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.ctakes.core.util.doc.SourceMetadataUtil;
import org.apache.ctakes.typesystem.type.structured.DocumentPath;
import org.apache.ctakes.typesystem.type.structured.SourceData;
import org.apache.ctakes.typesystem.type.textsem.EventMention;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.component.JCasAnnotator_ImplBase;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.stream.Stream;

import org.healthnlp.annotation.LabelStudioFileAnnotation;
import org.healthnlp.annotation.LabelStudioResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
@PipeBitInfo(
        name = "LabelStudioPreAnnotationWriter",
        description = "Creates a representation of Label Studio for a given note, writes them all to one JSON file at the end.",
        dependencies = { PipeBitInfo.TypeProduct.EVENT }
)
public class LabelStudioPreAnnotationWriter extends JCasAnnotator_ImplBase {
    private final Set<String> labelStudioIDs = new HashSet<>();
    static private final Logger LOGGER = LoggerFactory.getLogger( "LabelStudioPreAnnotationWriter" );
    private final SortedMap<Integer, LabelStudioFileAnnotation> documentIDtoFileAnnotation = new TreeMap<>();
    @Override
    public void process(JCas jCas) throws AnalysisEngineProcessException {
        LabelStudioFileAnnotation documentFileAnnotation = new LabelStudioFileAnnotation(jCas);
        int documentID = Integer.parseInt(getJCasFilename(jCas).split(",")[0]);
        documentIDtoFileAnnotation.put(documentID, documentFileAnnotation);
    }

    public static String getJCasFilename(JCas jCas){
        DocumentPath documentPath = JCasUtil.select( jCas, DocumentPath.class ).iterator().next();
        return FilenameUtils.getBaseName( documentPath.getDocumentPath() );
    }

    private Stream<LabelStudioResult> eventMentionToResults(EventMention eventMention){
        return Stream.empty();
    }

    private void updateResultID(LabelStudioResult result){
        int tries = 10;
        for (int i = 0; i < tries; i++){
            String candidate = getSaltString();
            if (!labelStudioIDs.contains(candidate)){
                result.setId(candidate);
                labelStudioIDs.add(candidate);
                return;
            }
        }
        LOGGER.error("Cound not set ID for {} after {} tries", result, tries);
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
    }
}
