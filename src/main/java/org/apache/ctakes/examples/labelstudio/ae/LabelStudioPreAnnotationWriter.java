package org.apache.ctakes.examples.labelstudio.ae;

import org.apache.commons.io.FilenameUtils;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.ctakes.core.resource.FileLocator;
import org.apache.ctakes.core.util.annotation.OntologyConceptUtil;
import org.apache.ctakes.typesystem.type.refsem.UmlsConcept;
import org.apache.ctakes.typesystem.type.structured.DocumentPath;
import org.apache.ctakes.typesystem.type.textsem.EventMention;
import org.apache.uima.UimaContext;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.component.JCasAnnotator_ImplBase;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.uima.resource.ResourceInitializationException;
import org.healthnlp.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
@PipeBitInfo(
        name = "LabelStudioPreAnnotationWriter",
        description = "Creates a representation of Label Studio for a given note, writes them all to one JSON file at the end.",
        dependencies = { PipeBitInfo.TypeProduct.EVENT }
)
public class LabelStudioPreAnnotationWriter extends JCasAnnotator_ImplBase {
    static private final Logger LOGGER = LoggerFactory.getLogger( "LabelStudioPreAnnotationWriter" );
    private final SortedMap<Integer, LabelStudioFileAnnotation> documentIDtoFileAnnotation = new TreeMap<>();
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
        LabelStudioFileAnnotation documentFileAnnotation = new LabelStudioFileAnnotation(jCas);
        int documentID = Integer.parseInt(getJCasFilename(jCas).split(",")[0]);
        documentIDtoFileAnnotation.put(documentID, documentFileAnnotation);
    }

    public static String getJCasFilename(JCas jCas){
        DocumentPath documentPath = JCasUtil.select( jCas, DocumentPath.class ).iterator().next();
        return FilenameUtils.getBaseName( documentPath.getDocumentPath() );
    }

    private Stream<? extends LabelStudioResult> eventMentionToResults(EventMention eventMention){
        Set<String> umlsConcepts = OntologyConceptUtil.getUmlsConcepts(eventMention)
                .stream()
                .map( UmlsConcept::getCui )
                .collect( Collectors.toSet() );
        boolean isCTAE = umlsConcepts
                .stream()
                .anyMatch(e -> this.ctaeTerms.contains(e));
        boolean isRT = umlsConcepts
                .stream()
                .anyMatch(e -> this.rtTerms.contains(e));
        Stream<LabelsResult> coreEvent = Stream.empty();
        if (isCTAE && isRT){
            LOGGER.info("{} from {} is has CUIS {} which evidence both CTAE and RT - making a duplicate entry",
                    eventMention.getCoveredText().strip(),
                    getJCasFilename(eventMention.getJCas()),
                    umlsConcepts.stream().sorted().collect(Collectors.joining(", ")));
            coreEvent = Stream.of(
                    // RT then CTAE
                    new LabelsResult(), new LabelsResult());
        } else if (isCTAE) {
            coreEvent = Stream.of(
                    // CTAE
                    new LabelsResult());
        } else if (isRT){
            coreEvent = Stream.of(
                    // RT
                    new LabelsResult());
        } else {
            LOGGER.info("{} from {} is has CUIS {} none of which evidence CTAE or RT - returning nothing",
                    eventMention.getCoveredText().strip(),
                    getJCasFilename(eventMention.getJCas()),
                    umlsConcepts.stream().sorted().collect(Collectors.joining(", ")));
            return coreEvent;
        }
        Stream<TextAreaResult> eventCUIs = umlsConcepts
                .stream()
                .map(e -> new TextAreaResult());
        Stream<ChoicesResult> eventDTR = Stream.of(new ChoicesResult());
        return Stream.of(coreEvent, eventCUIs, eventDTR)
                .flatMap(Function.identity());
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

    private Set<String> getTerms(String filterList) {
        if ( filterList != null && !filterList.isEmpty() ) {
            try ( InputStream descriptorStream = FileLocator.getAsStream( filterList ) ) {
                return new BufferedReader(
                        new InputStreamReader(
                                descriptorStream,
                                StandardCharsets.UTF_8
                        )
                ).lines()
                        .map( String::toLowerCase )
                        .map( String::trim )
                        .collect( Collectors.toSet() );
            } catch ( IOException e ) {
                throw new RuntimeException( e );
            }
        } else {
            LOGGER.info( "Missing Filter List, Using Empty List" );
            return new HashSet<>();
        }
    }
}
