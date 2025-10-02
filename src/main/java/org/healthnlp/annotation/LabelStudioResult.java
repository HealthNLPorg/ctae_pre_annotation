package org.healthnlp.annotation;

public class LabelStudioResult implements Comparable<LabelStudioResult>{
    public String id;
    public LabelStudioResultValue value;
    public String from_name;
    public String to_name;
    public String type;
    public String origin;


    public void setId(String id){
        this.id = id;
    }

    @Override
    public int compareTo(final LabelStudioResult other) {
        return this.value.start - other.value.start;
    }
}
