package org.healthnlp.annotation.labelstudio.annotation;

import org.apache.uima.jcas.JCas;
import org.healthnlp.annotation.labelstudio.data.LabelStudioData;

import java.util.LinkedList;
import java.util.List;
import java.util.Set;

import static org.healthnlp.annotation.utils.Utils.getJCasFilename;

public class LabelStudioFileAnnotation implements Comparable<LabelStudioFileAnnotation> {
    public int id;
    public List<LabelStudioAnnotation> annotations;
    public String file_upload;
    public LabelStudioData data;
    public List<String> drafts = new LinkedList<>();
    public List<String> predictions = new LinkedList<>();

    public void setId(int id) {
        this.id = id;
    }

    public LabelStudioFileAnnotation(JCas jCas, Set<String> ctaeTerms, Set<String> rtTerms){
        this.file_upload = getJCasFilename(jCas);
        this.data = new LabelStudioData(jCas.getDocumentText());
        this.annotations = List.of(new LabelStudioAnnotation(jCas, ctaeTerms, rtTerms));
    }

    @Override
    public int compareTo(LabelStudioFileAnnotation o) {
        return this.file_upload.compareTo(o.file_upload);
    }
}
