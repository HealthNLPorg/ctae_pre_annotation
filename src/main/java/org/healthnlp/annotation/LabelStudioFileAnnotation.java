package org.healthnlp.annotation;

import org.apache.ctakes.examples.labelstudio.ae.LabelStudioPreAnnotationWriter;
import org.apache.uima.jcas.JCas;

import java.util.LinkedList;
import java.util.List;

public class LabelStudioFileAnnotation {
    public int id;
    public List<LabelStudioAnnotation> annotations;
    public String file_upload;
    public LabelStudioData data;
    public List<String> drafts = new LinkedList<>();
    public List<String> predictions = new LinkedList<>();

    public void setId(int id) {
        this.id = id;
    }

    public LabelStudioFileAnnotation(JCas jCas){
        this.file_upload = LabelStudioPreAnnotationWriter.getJCasFilename(jCas);
        this.data = new LabelStudioData(jCas.getDocumentText());
        this.annotations = List.of(new LabelStudioAnnotation(jCas));
    }
}
