package org.apache.ctakes.examples.chemotime.ae;

import org.apache.commons.io.FilenameUtils;
import org.apache.ctakes.core.pipeline.PipeBitInfo;
import org.apache.ctakes.core.util.StringUtil;
import org.apache.ctakes.core.util.doc.SourceMetadataUtil;
import org.apache.ctakes.temporal.ae.DocTimeApproximator;
import org.apache.ctakes.typesystem.type.structured.DocumentPath;
import org.apache.ctakes.typesystem.type.structured.SourceData;
import org.apache.uima.analysis_engine.AnalysisEngineProcessException;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.Optional;

@PipeBitInfo (
      name = "DCTAnnotator ( TxTimelines )",
      description = "Gets Document time from the filename or the header if it's a UPMC note.",
      role = PipeBitInfo.Role.SPECIAL
)

public class DCTAnnotator extends org.apache.uima.fit.component.JCasAnnotator_ImplBase {
   final static private Logger LOGGER = LoggerFactory.getLogger( "DCTAnnotator" );
   final static private DocTimeApproximator _approximator = new DocTimeApproximator();


   @Override
   public void process( JCas jCas ) throws AnalysisEngineProcessException {
      // could use some refactoring
      final SourceData sourceData = SourceMetadataUtil.getOrCreateSourceData( jCas );

      DocumentPath documentPath = JCasUtil.select( jCas, DocumentPath.class ).iterator().next();

      String fileName = FilenameUtils.getBaseName( documentPath.getDocumentPath() );
      String[] fileNameElements = StringUtil.fastSplit( fileName, '_' );
      if ( fileNameElements.length >= 3 ) {

         String[] possibleDate = StringUtil.fastSplit( fileNameElements[ 2 ], '-' );

         if ( possibleDate.length == 3 ) {

            int month = Integer.parseInt( possibleDate[ 0 ] );
            int day = Integer.parseInt( possibleDate[ 1 ] );
            int year = Integer.parseInt( possibleDate[ 2 ] );

            String docTime = year + "-" + String.format( "%02d", month ) + "-" + String.format( "%02d", day );

            sourceData.setSourceOriginalDate( docTime );
            LOGGER.info( "DeepPhe Spec Note {} Time is Set to {}", fileName, docTime );
            return;
         }
         LOGGER.info( "DeepPhe Non-Spec Note {}: Ensure is UPMC ", fileName );
      }

      // Otherwise this is a UPMC note
      Optional<String> principalDateLine = Arrays.stream( jCas.getDocumentText().split( "\n" ) )
                                                 .filter( s -> s.startsWith( "Principal Date" ) )
                                                 .findFirst();

      String rawDCT = principalDateLine
            .map(
                  s -> s.replaceAll(
                        "\\D",
                        ""
                  )
            )
            .orElse( "UNK" );

      if ( rawDCT.equals( "UNK" ) ) {
         LOGGER.warn(
               "DeepPhe Non-Spec Note {}: Could Not Find Principal Date In Header! Resorting to DocTimeApproximator",
               fileName );
         _approximator.process( jCas );
         return;
      }

      assert rawDCT.length() == 8; // YYYYMMDD
      // Sometimes I forget how substring works
      String year = rawDCT.substring( 0, 4 );
      String month = rawDCT.substring( 4, 6 );
      String date = rawDCT.substring( 6, 8 );

      String docTime = year + "-" + month + "-" + date;
      sourceData.setSourceOriginalDate( docTime );
      LOGGER.info( "DeepPhe Non-Spec Note {} Time is Set to {}", fileName, docTime );
   }
}
