package org.healthnlp.annotation.utils;

import org.apache.commons.io.FilenameUtils;
import org.apache.ctakes.typesystem.type.structured.DocumentPath;
import org.apache.ctakes.typesystem.type.textsem.IdentifiedAnnotation;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;

import java.util.List;
import java.util.Random;

public class Utils {
    public static String getJCasFilename(JCas jCas){
        DocumentPath documentPath = JCasUtil.select( jCas, DocumentPath.class ).iterator().next();
        return FilenameUtils.getBaseName( documentPath.getDocumentPath() );
    }

    public static List<Integer> getAnnotationIndices(IdentifiedAnnotation identifiedAnnotation) {
        return List.of(identifiedAnnotation.getBegin(), identifiedAnnotation.getEnd());
    }

    public static String getSaltString() {
        String SALTCHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_";
        StringBuilder salt = new StringBuilder();
        Random rnd = new Random();
        while (salt.length() < 10) { // length of the random string.
            int index = (int) (rnd.nextFloat() * SALTCHARS.length());
            salt.append(SALTCHARS.charAt(index));
        }
        return salt.toString();
    }
}
