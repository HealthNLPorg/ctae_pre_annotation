package org.healthnlp.annotation;

import org.apache.uima.jcas.JCas;

import java.util.List;

public class LabelStudioAnnotation {
    public int id;
    public List<LabelStudioResult> result;

    public void setId(int id) {
        this.id = id;
    }

    public LabelStudioAnnotation(JCas jCas){
    }
}
