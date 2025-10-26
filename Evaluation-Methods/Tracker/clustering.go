package tracker

import (
	"database/sql"
	"encoding/json"
	"time"

	"github.com/guregu/null"
)

type EvaluationLog struct {
	ID                int             `db:"id"`
	QuestionID        string          `db:"question_id"`
	QuestionText      string          `db:"question_text"`
	ResponseText      string          `db:"response_text"`
	Scores            json.RawMessage `db:"scores"`
	Timestamp         time.Time       `db:"timestamp"`
	QuestionEmbedding json.RawMessage `db:"question_embedding"`
	ResponseEmbedding json.RawMessage `db:"response_embedding"`
	ClusterID         sql.NullInt64   `db:"cluster_id"`
	TemporalOrder     sql.NullInt64   `db:"temporal_order"`
}

type ConversationEntry struct {
	QuestionID        string         `json:"question_id"`
	QuestionText      string         `json:"question_text"`
	ResponseText      string         `json:"response_text"`
	Scores            map[string]int `json:"scores"`
	Timestamp         time.Time      `json:"timestamp"`
	QuestionEmbedding []byte         `json:"question_embedding"`
	ResponseEmbedding []byte         `json:"response_embedding"`
	ClusterID         null.Int       `json:"cluster_id"`
	TemporalOrder     null.Int       `json:"temporal_order"`
}

func main() {

}
