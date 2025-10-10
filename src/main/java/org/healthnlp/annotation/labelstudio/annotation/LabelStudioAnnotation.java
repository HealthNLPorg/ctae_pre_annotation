package org.healthnlp.annotation.labelstudio.annotation;

import org.apache.ctakes.core.util.annotation.OntologyConceptUtil;
import org.apache.ctakes.typesystem.type.refsem.Event;
import org.apache.ctakes.typesystem.type.refsem.EventProperties;
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
import org.healthnlp.annotation.utils.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.healthnlp.annotation.utils.Utils.getAnnotationIndices;
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
                .collect(Collectors.groupingBy(Utils::getAnnotationIndices))
                .values()
                .stream()
                .flatMap(this::spanMentionsToResults)
                //.sorted()
                .collect(Collectors.toList());
    }

    private Stream<? extends Result> spanMentionsToResults(
            List<EventMention> eventMentions){
        EventMention defaultMention = eventMentions.get(0);
        List<Integer> targetIndices = getAnnotationIndices(defaultMention);

        Predicate<List<Integer>> matchesTargetIndices =
                indices -> indices.equals(targetIndices);

        assert eventMentions
                .stream()
                .map(Utils::getAnnotationIndices)
                .allMatch(matchesTargetIndices);

        Set<String> CUIs = eventMentions.stream()
                .map(OntologyConceptUtil::getUmlsConcepts)
                .flatMap(Collection::stream)
                .map( UmlsConcept::getCui )
                .collect( Collectors.toSet() );

        Set<String> TUIs =  eventMentions.stream()
                .map(OntologyConceptUtil::getUmlsConcepts)
                .flatMap(Collection::stream)
                .map( UmlsConcept::getTui )
                .collect( Collectors.toSet() );

        Set<String> DTRs = eventMentions
                .stream()
                .map(EventMention::getEvent)
                .map(Event::getProperties)
                .map(EventProperties::getDocTimeRel)
                .collect(Collectors.toSet());

        // They're currently mutually exclusive but who knows
        boolean isCTAE = TUIs.contains("T033");
        boolean isRT = TUIs.contains("T061");
        Stream<LabelsResult> coreEvent = Stream.empty();
        if (isCTAE && isRT){
            LOGGER.info("{} from {} is has CUIS {} which evidence both CTAE and RT - making a duplicate entry",
                    defaultMention.getCoveredText().strip(),
                    getJCasFilename(defaultMention.getJCas()),
                    CUIs.stream().sorted().collect(Collectors.joining(", ")));
            coreEvent = Stream.of(
                    // RT then CTAE
                    new LabelsResult(
                            defaultMention.getBegin(),
                            defaultMention.getEnd(),
                            defaultMention.getCoveredText(),
                            List.of("Radiotherapy Treatment")),
                    new LabelsResult(
                            defaultMention.getBegin(),
                            defaultMention.getEnd(),
                            defaultMention.getCoveredText(),
                            List.of("Adverse Event")));
        } else if (isCTAE) {
            coreEvent = Stream.of(
                    // CTAE
                    new LabelsResult(
                            defaultMention.getBegin(),
                            defaultMention.getEnd(),
                            defaultMention.getCoveredText(),
                            List.of("Adverse Event")));
        } else if (isRT){
            coreEvent = Stream.of(
                    // RT
                    new LabelsResult(
                            defaultMention.getBegin(),
                            defaultMention.getEnd(),
                            defaultMention.getCoveredText(),
                            List.of("Radiotherapy Treatment")));
        } else {
            LOGGER.info("{} from {} is has CUIS {} none of which evidence CTAE or RT - returning nothing",
                    defaultMention.getCoveredText().strip(),
                    getJCasFilename(defaultMention.getJCas()),
                    CUIs.stream().sorted().collect(Collectors.joining(", ")));
            return coreEvent;
        }

        TextAreaResult cuiEvent = new TextAreaResult(
                defaultMention.getBegin(),
                defaultMention.getEnd(),
                CUIs.stream().toList());

        ChoicesResult eventDTR = new ChoicesResult(
                defaultMention.getBegin(),
                defaultMention.getEnd(),
                defaultMention.getCoveredText(),
                DTRs.stream().toList()
        );
        return Stream.concat(
                Stream.of(cuiEvent, eventDTR),
                coreEvent
        );
    }
}
