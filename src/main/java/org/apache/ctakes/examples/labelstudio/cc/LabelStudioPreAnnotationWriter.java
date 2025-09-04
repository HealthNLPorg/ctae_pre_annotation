package org.apache.ctakes.examples.labelstudio.cc;

import org.apache.ctakes.core.cc.AbstractJCasFileWriter;
import org.apache.uima.jcas.JCas;

import java.io.IOException;
// Adhering to https://labelstud.io/guide/tasks#Basic-Label-Studio-JSON-format
public class LabelStudioPreAnnotationWriter extends AbstractJCasFileWriter {
    @Override
    public void writeFile(JCas data, String outputDir, String documentId, String fileName) throws IOException {

    }
}
