package org.healthnlp.annotation.labelstudio.annotation;

import org.apache.ctakes.core.util.annotation.OntologyConceptUtil;
import org.apache.ctakes.typesystem.type.refsem.UmlsConcept;
import org.apache.ctakes.typesystem.type.textsem.EventMention;
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

    public LabelStudioAnnotation(JCas jCas, Set<String> ctaeTerms, Set<String> rtTerms){
        result = JCasUtil.select(jCas, EventMention.class)
                .stream()
                .flatMap(e -> this.eventMentionToResults(e, ctaeTerms, rtTerms))
                .sorted()
                .collect(Collectors.toList());
    }

    private Stream<? extends Result> eventMentionToResults(EventMention eventMention, Set<String> ctaeTerms, Set<String> rtTerms){
        Set<String> umlsConcepts = OntologyConceptUtil.getUmlsConcepts(eventMention)
                .stream()
                .map( UmlsConcept::getCui )
                .collect( Collectors.toSet() );
        boolean isCTAE = umlsConcepts
                .stream()
                .anyMatch( ctaeTerms::contains );
        boolean isRT = umlsConcepts
                .stream()
                .anyMatch( rtTerms::contains );
        Stream<LabelsResult> coreEvent = Stream.empty();
        if (isCTAE && isRT){
            LOGGER.info("{} from {} is has CUIS {} which evidence both CTAE and RT - making a duplicate entry",
                    eventMention.getCoveredText().strip(),
                    getJCasFilename(eventMention.getJCas()),
                    umlsConcepts.stream().sorted().collect(Collectors.joining(", ")));
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
                    umlsConcepts.stream().sorted().collect(Collectors.joining(", ")));
            return coreEvent;
        }
        Stream<TextAreaResult> eventCUIs = umlsConcepts
                .stream()
                .map(e -> new TextAreaResult(
                        eventMention.getBegin(), eventMention.getEnd(), List.of(e)));
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
