namespace MedicalSystem.Models
{
    public class MedicalRecord
    {
        public int Id { get; set; } // Primary Key
        public int PatientId { get; set; } // Foreign Key

        public required string DiseaseName { get; set; }
        public DateTime StartDate { get; set; }
        public DateTime? EndDate { get; set; }

        // Corrected Navigation Property for Lazy Loading
        public virtual Patient Patient { get; set; }
    }
}
