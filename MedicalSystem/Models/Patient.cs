namespace MedicalSystem.Models
{
    public class Patient
    {
        public int Id { get; set; } // Primary Key

        public required string PatientID { get; set; } // Unique Identifier
        public required string Name { get; set; }
        public required string Surname { get; set; }
        public required DateTime DateOfBirth { get; set; }
        public required char Sex { get; set; }

        // Corrected Navigation Properties for Lazy Loading
        public virtual List<MedicalRecord> MedicalRecords { get; set; } = new();
        public virtual List<Checkup> Checkups { get; set; } = new();
    }
}

