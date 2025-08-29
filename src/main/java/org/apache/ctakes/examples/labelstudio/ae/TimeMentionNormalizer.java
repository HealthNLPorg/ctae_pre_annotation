package org.apache.ctakes.examples.labelstudio.ae;

import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.ctakes.core.util.CalendarUtil;
import org.apache.ctakes.core.util.StringUtil;
import org.apache.ctakes.core.util.annotation.OntologyConceptUtil;
import org.apache.ctakes.core.util.doc.DocIdUtil;
import org.apache.ctakes.core.util.doc.SourceMetadataUtil;
import org.apache.ctakes.core.util.log.DotLogger;
import org.apache.ctakes.typesystem.type.refsem.Time;
import org.apache.ctakes.typesystem.type.textsem.TimeMention;
import org.apache.uima.UimaContext;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.descriptor.ConfigurationParameter;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.apache.uima.resource.ResourceInitializationException;
import org.clulab.timenorm.scfg.TimeSpan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import static org.apache.ctakes.core.util.CalendarUtil.NULL_CALENDAR;

@PipeBitInfo(
        name = "TimeMentionNormalizer",
        description = "Normalizes temporal expressions in a document.",
        role = PipeBitInfo.Role.SPECIAL,
        dependencies = { PipeBitInfo.TypeProduct.EVENT, PipeBitInfo.TypeProduct.TIMEX }
)
public class TimeMentionNormalizer extends org.apache.uima.fit.component.JCasAnnotator_ImplBase {
    static private final Logger LOGGER = LoggerFactory.getLogger( "TimeMentionNormalizer" );

    public static final String PARAM_TUIS = "EventTuis";

    @ConfigurationParameter(
                            name = PARAM_TUIS,
                            description = "TUIs for valid temporal events.",
                            defaultValue = "T061",
                            mandatory = false
    )
    private String _tuis;

    public static final String PARAM_TIMEOUT = "NormalizeTimeout";
    public static final int DEFAULT_TIMEOUT = 5;
    @ConfigurationParameter(
                            name = PARAM_TIMEOUT,
                            description = "Seconds to wait before canceling normalization of a time mention.",
                            mandatory = false,
          defaultValue = "" + DEFAULT_TIMEOUT
    )
    private String _timeout;
    private Set<String> _tuiSet;

    static private final Pattern WHITE_CHAR_PATTERN = Pattern.compile( "\\s" );

    private TimeoutTimeNormalizer _timeoutNormalizer;

    @Override
    public void initialize( final UimaContext context ) throws ResourceInitializationException {
        super.initialize( context );
        _tuiSet = Arrays.stream( StringUtil.fastSplit( _tuis, ',' ) )
                        .map( String::toUpperCase )
                        .collect( Collectors.toSet() );
        _timeoutNormalizer = new TimeoutTimeNormalizer();
        try {
            final int timeoutInt = parseInt( _timeout );
            if ( timeoutInt > Integer.MIN_VALUE ) {
                LOGGER.info( "Using timeout: {}", timeoutInt );
                _timeoutNormalizer.setTimeout( timeoutInt * 1000 );
            }
        } catch ( IllegalArgumentException ignore ) {
        }
    }

    @Override
    public void process( final JCas jCas ) throws AnalysisEngineProcessException {
        final String docId = DocIdUtil.getDocumentID( jCas );
        if ( !hasWantedTuis( jCas ) ) {
            LOGGER.info( "No events in {} with wanted TUIs {}.", docId, _tuis );
            return;
        }
        final List<TimeMention> timeMentions = JCasUtil
              .select( jCas, TimeMention.class )
              .stream()
              .toList();
        if ( timeMentions.isEmpty() ) {
            LOGGER.info( "No time mentions in {}.", docId );
            return;
        }
        final TimeSpan dct = getDocTime( jCas, docId );
        try ( DotLogger dotter = new DotLogger() ) {
            timeMentions.forEach( t -> normalize( jCas, dct, t ) );
        } catch ( IOException ignored ) {
        }
    }

    private boolean hasWantedTuis( final JCas jCas ) {
        if ( _tuiSet.isEmpty() ) {
            // All TUIs are acceptable.
            return true;
        }
        // We don't expect the document to have a lot of annotations, so this should be quick.
        return OntologyConceptUtil.getTuis( jCas ).stream().anyMatch( _tuiSet::contains );
    }

    static private TimeSpan getDocTime( final JCas jCas, final String docId ) {
        // This relies upon the source original date having been put in the jcas.
        final String docTime = SourceMetadataUtil.getOrCreateSourceData( jCas )
                                                 .getSourceOriginalDate();
        if ( docTime == null || docTime.isEmpty() ) {
            LOGGER.warn( "No Document Creation Time for {}", docId );
            // Consider using DocTimeApproximator to set it if it has not already been set.
            return null;
        }
        if ( docTime.length() == 8 && parseInt( docTime ) > Integer.MIN_VALUE ) {
            final int maybeYear =  Integer.parseInt( docTime.substring( 0, 4 ) );
            if ( maybeYear > 1900 && maybeYear < 2050 ) {
                // Possibly DocTimeApproximator generated.
                return TimeSpan.of(
                      maybeYear,
                      Integer.parseInt( docTime.substring( 4, 6 ) ),
                      Integer.parseInt( docTime.substring( 6, 8 ) ) );
            }
        }
        final String[] docTimeComponents = StringUtil.fastSplit( docTime, '-' );
        if ( docTimeComponents.length == 3 ) {
            // DCTAnnotator generated ( should be this in all cases )
            return TimeSpan.of(
                  Integer.parseInt( docTimeComponents[ 0 ] ),
                  Integer.parseInt( docTimeComponents[ 1 ] ),
                  Integer.parseInt( docTimeComponents[ 2 ] ) );
        }
        final Calendar dtcalendar = CalendarUtil.getCalendar( docTime );
        final int year = dtcalendar.get( Calendar.DAY_OF_MONTH );
        final int month = dtcalendar.get( Calendar.MONTH ) + 1;
        final int day = dtcalendar.get( Calendar.YEAR );
        if ( !NULL_CALENDAR.equals( dtcalendar ) ) {
            return TimeSpan.of( year, month, day );
        }
        return null;
    }


    private void normalize( final JCas jCas, final TimeSpan DCT, final TimeMention timeMention ) {
        final String normalizedTimex = getTimeML( DCT, timeMention );
        if ( normalizedTimex.isEmpty() ) {
            return;
        }
        Time time = timeMention.getTime();
        if ( time == null ) {
            time = new Time( jCas );
            time.addToIndexes();
        }
        time.setNormalizedForm( normalizedTimex );
        timeMention.setTime( time );
    }

    private String getTimeML( final TimeSpan DCT, final TimeMention timeMention ) {
        final String rawDateText = timeMention.getCoveredText();
        final String[] rawDateElements = StringUtil.fastSplit( rawDateText, '/' );
        final List<Integer> dateElements = new ArrayList<>();
        for ( String rawElement : rawDateElements ) {
            try {
                final int elem = Integer.parseInt( rawElement );
                dateElements.add( elem );
            } catch ( Exception ignored ) {}
        }
        // can also do this in a way that grabs stragglers
        if ( dateElements.size() == 3 && rawDateElements.length == 3 ) {
            // avoiding TimeNorm's issues with component order
            // ambiguity since these notes were all generated
            // at American hospitals and therefore modulo mistakes
            // will all use the American convention
            final int month = dateElements.get( 0 );
            final int date = dateElements.get( 1 );
            final int raw_year = dateElements.get( 2 );
            final int year = ( rawDateElements[2].length() == 2 ) ? raw_year + 2000 : raw_year;
            try {
                final TimeSpan parsedDate = TimeSpan.of( year, month, date );
                return parsedDate.timeMLValue();
            } catch ( Exception ignored ) {
            }
        }
        final String unnormalizedTimex
              = String.join(" ", WHITE_CHAR_PATTERN.split( timeMention.getCoveredText() ) );
        return _timeoutNormalizer.normalizeTime( unnormalizedTimex, DCT );
    }

    /**
     * @param text -
     * @return positive int value of text or {@link Integer#MIN_VALUE} if not possible.
     */
    static private int parseInt( final String text ) {
        if ( text == null || text.isEmpty() ) {
            return Integer.MIN_VALUE;
        }
        for ( char c : text.toCharArray() ) {
            if ( !Character.isDigit( c ) ) {
                return Integer.MIN_VALUE;
            }
        }
        try {
            return Integer.parseInt( text );
        } catch ( NumberFormatException nfE ) {
            return Integer.MIN_VALUE;
        }
    }

}
