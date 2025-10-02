package org.healthnlp.annotation;

import org.apache.uima.jcas.JCas;

import java.util.Collection;

public class LabelStudioAnnotation {
    public int id;
    public Collection<LabelStudioResult> results;

    LabelStudioFileAnnotation(JCas jCas){

    }
}
