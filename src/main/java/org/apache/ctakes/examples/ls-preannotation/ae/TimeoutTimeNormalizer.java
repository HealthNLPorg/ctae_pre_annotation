package org.apache.ctakes.examples.chemotime.ae;

import org.clulab.timenorm.scfg.TemporalExpressionParser;
import org.clulab.timenorm.scfg.TimeSpan;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Closeable;
import java.util.concurrent.*;

/**
 * Runs the timenorm normalizer in a thread that is canceled if it takes longer than a given timeout.
 * @author SPF , chip-nlp
 * @since {12/20/2024}
 */
public class TimeoutTimeNormalizer  implements Closeable {

   static private final Logger LOGGER = LoggerFactory.getLogger( "TimeoutTimeNormalizer" );

   static private final int DEFAULT_TIMEOUT_MILLIS = 1000;
   static private final int MIN_TIMEOUT_MILLIS = 100;
   static private final int MAX_TIMEOUT_MILLIS = 10000;

   static private final TemporalExpressionParser TIME_NORMALIZER = TemporalExpressionParser.en();

   private final ExecutorService _executor;
   private int _timeoutMillis;

   /**
    * Uses the default timeout of 1000 milliseconds
    *
    * @throws IllegalArgumentException if the timeout is out of bounds
    */
   public TimeoutTimeNormalizer() {
      this( DEFAULT_TIMEOUT_MILLIS );
   }

   /**
    *
    * @param timeoutMillis milliseconds at which the regex match should abort, between 100 and 10000
    * @throws IllegalArgumentException if the timeout is out of bounds
    */
   public TimeoutTimeNormalizer( final int timeoutMillis ) throws IllegalArgumentException {
      setTimeout( timeoutMillis );
      _executor = Executors.newSingleThreadExecutor();
   }

   public void setTimeout( final int timeoutMillis ) throws IllegalArgumentException {
      if ( timeoutMillis < MIN_TIMEOUT_MILLIS || timeoutMillis > MAX_TIMEOUT_MILLIS ) {
         throw new IllegalArgumentException( "Timeout must be between "
               + MIN_TIMEOUT_MILLIS + " and " + MAX_TIMEOUT_MILLIS );
      }
      _timeoutMillis = timeoutMillis;
   }

   public String normalizeTime( final String timeText, final TimeSpan doctime ) {
      final Callable<String> callable = new NormalizeCallable( timeText, doctime );
      final Future<String> future = _executor.submit( callable );
      try {
         return future.get( _timeoutMillis, TimeUnit.MILLISECONDS );
      } catch ( InterruptedException | ExecutionException | TimeoutException multE ) {
         LOGGER.debug( "Timed out while normalizing time {}", timeText );
         if ( !future.cancel( true ) ) {
            LOGGER.error( "Timed out but could not be cancelled while normalizing time {} ", timeText );
         }
      }
      if ( future.isCancelled() ) {
         LOGGER.error( "Cancelled while normalizing time {}", timeText );
      } else if ( !future.isDone() ) {
         LOGGER.error( "Not cancelled but didn't complete while normalizing time {}", timeText );
      }
      return "";
   }


   /**
    * shut down the executor
    * {@inheritDoc}
    */
   @Override
   public void close() {
      _executor.shutdownNow();
   }


   /**
//    * Simple Callable that runs a temporal normalizer on text
    */
   static private final class NormalizeCallable implements Callable<String> {
      final private String _timeText;
      final private TimeSpan _doctime;
      private NormalizeCallable( final String timeText, final TimeSpan doctime ) {
         _timeText = timeText;
         _doctime = doctime;
      }

      /**
       * {@inheritDoc}
       *
       * @return matcher if there is another find, else null
       */
      @Override
      public String call() {
         try {
            return TIME_NORMALIZER.parse( _timeText, _doctime ).get().timeMLValue();
         } catch ( Exception ignored ) {}
         return "";
      }
   }


}
