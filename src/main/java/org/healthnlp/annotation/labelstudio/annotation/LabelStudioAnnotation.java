package org.healthnlp.annotation.labelstudio.annotation;

import org.apache.uima.jcas.JCas;
import org.healthnlp.annotation.labelstudio.result.Result;

import java.util.List;

public class LabelStudioAnnotation {
    public int id;
    public List<Result> result;

    public void setId(int id) {
        this.id = id;
    }

    public LabelStudioAnnotation(JCas jCas){
    }
}
