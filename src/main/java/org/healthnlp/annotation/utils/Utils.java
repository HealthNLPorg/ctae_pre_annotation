package org.healthnlp.annotation.utils;

import org.apache.commons.io.FilenameUtils;
import org.apache.ctakes.core.resource.FileLocator;
import org.apache.ctakes.typesystem.type.structured.DocumentPath;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

public class Utils {
    static private final Logger LOGGER = LoggerFactory.getLogger( "Utils" );
    public static String getJCasFilename(JCas jCas){
        DocumentPath documentPath = JCasUtil.select( jCas, DocumentPath.class ).iterator().next();
        return FilenameUtils.getBaseName( documentPath.getDocumentPath() );
    }

    public static Set<String> getTerms(String filterList) {
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
            LOGGER.info( "Missing filter terms {}, Using the empty set", filterList );
            return new HashSet<>();
        }
    }
}
