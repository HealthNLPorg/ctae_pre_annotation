package org.healthnlp.annotation;

import org.apache.ctakes.examples.labelstudio.ae.LabelStudioPreAnnotationWriter;
import org.apache.uima.jcas.JCas;

import java.util.Collection;

public class LabelStudioFileAnnotation {
    public int id;
    public Collection<LabelStudioAnnotation> annotations;

    public LabelStudioFileAnnotation(JCas jCas){
        String fileName = LabelStudioPreAnnotationWriter.getJCasFilename(jCas);
        String documentText = jCas.getDocumentText();
    }
}
