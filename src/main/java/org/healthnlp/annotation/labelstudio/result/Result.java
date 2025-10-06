package org.healthnlp.annotation.labelstudio.result;

import org.apache.ctakes.typesystem.type.textsem.EventMention;
import org.healthnlp.annotation.labelstudio.result.value.Value;

public class Result implements Comparable<Result>{
    public String id;
    public Value value;
    public String from_name;
    public String to_name;
    public String type;
    public String origin;

    public void setId(String id){
        this.id = id;
    }

    @Override
    public int compareTo(final Result other) {
        return this.value.start - other.value.start;
    }
}
