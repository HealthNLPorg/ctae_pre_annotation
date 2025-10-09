package org.healthnlp.annotation.labelstudio.annotation;

import org.apache.ctakes.core.util.annotation.OntologyConceptUtil;
import org.apache.ctakes.typesystem.type.refsem.UmlsConcept;
import org.apache.ctakes.typesystem.type.textsem.EventMention;
import org.apache.ctakes.typesystem.type.textsem.ProcedureMention;
import org.apache.ctakes.typesystem.type.textsem.SignSymptomMention;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.healthnlp.annotation.labelstudio.result.ChoicesResult;
import org.healthnlp.annotation.labelstudio.result.LabelsResult;
import org.healthnlp.annotation.labelstudio.result.Result;
import org.healthnlp.annotation.labelstudio.result.TextAreaResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.healthnlp.annotation.utils.Utils.getJCasFilename;

public class LabelStudioAnnotation {
    static private final Logger LOGGER = LoggerFactory.getLogger( "LabelStudioAnnotation" );

    public int id;
    public List<Result> result;

    public void setId(int id) {
        this.id = id;
    }

    public LabelStudioAnnotation(JCas jCas){
        result = Stream.concat(JCasUtil.select(jCas, SignSymptomMention.class).stream(),
                        JCasUtil.select(jCas, ProcedureMention.class).stream())
                .flatMap(this::eventMentionToResults)
                //.sorted()
                .collect(Collectors.toList());
    }

    private Stream<? extends Result> eventMentionToResults(
            EventMention eventMention){
        Set<String> CUIs = OntologyConceptUtil.getUmlsConcepts(eventMention)
                .stream()
                .map( UmlsConcept::getCui )
                .collect( Collectors.toSet() );
        Set<String> TUIs =  OntologyConceptUtil.getUmlsConcepts(eventMention)
                .stream()
                .map( UmlsConcept::getTui )
                .collect( Collectors.toSet() );
        // They're currently mutually exclusive but who knows
        boolean isCTAE = TUIs.contains("T033");
        boolean isRT = TUIs.contains("T061");
        Stream<LabelsResult> coreEvent = Stream.empty();
        if (isCTAE && isRT){
            LOGGER.info("{} from {} is has CUIS {} which evidence both CTAE and RT - making a duplicate entry",
                    eventMention.getCoveredText().strip(),
                    getJCasFilename(eventMention.getJCas()),
                    CUIs.stream().sorted().collect(Collectors.joining(", ")));
            coreEvent = Stream.of(
                    // RT then CTAE
                    new LabelsResult(
                            eventMention.getBegin(),
                            eventMention.getEnd(),
                            eventMention.getCoveredText(),
                            List.of("Radiotherapy Treatment")),
                    new LabelsResult(
                            eventMention.getBegin(),
                            eventMention.getEnd(),
                            eventMention.getCoveredText(),
                            List.of("Adverse Event")));
        } else if (isCTAE) {
            coreEvent = Stream.of(
                    // CTAE
                    new LabelsResult(
                            eventMention.getBegin(),
                            eventMention.getEnd(),
                            eventMention.getCoveredText(),
                            List.of("Adverse Event")));
        } else if (isRT){
            coreEvent = Stream.of(
                    // RT
                    new LabelsResult(
                            eventMention.getBegin(),
                            eventMention.getEnd(),
                            eventMention.getCoveredText(),
                            List.of("Radiotherapy Treatment")));
        } else {
            LOGGER.info("{} from {} is has CUIS {} none of which evidence CTAE or RT - returning nothing",
                    eventMention.getCoveredText().strip(),
                    getJCasFilename(eventMention.getJCas()),
                    CUIs.stream().sorted().collect(Collectors.joining(", ")));
            return coreEvent;
        }
        Function<String, TextAreaResult> CUIToLabelStudioResult = cui -> new TextAreaResult(
                eventMention.getBegin(),
                eventMention.getEnd(),
                List.of(cui));
        Stream<TextAreaResult> eventCUIs = CUIs
                .stream()
                .map(CUIToLabelStudioResult);
        Stream<ChoicesResult> eventDTR = Stream.of(
                new ChoicesResult(
                        eventMention.getBegin(),
                        eventMention.getEnd(),
                        eventMention.getCoveredText(),
                        List.of(eventMention.getEvent().getProperties().getDocTimeRel())
                ));
        return Stream.of(coreEvent, eventCUIs, eventDTR)
                .flatMap(Function.identity());
    }
}
