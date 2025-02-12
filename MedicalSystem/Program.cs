using MedicalSystem.Data;
using MedicalSystem.Models;
using MedicalSystem.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualStudio.Web.CodeGenerators.Mvc.Templates.BlazorIdentity.Pages;
using Minio;

var builder = WebApplication.CreateBuilder(args);

// Register MinIO Client
builder.Services.AddSingleton<IMinioClient>(sp =>
{
    var configuration = sp.GetRequiredService<IConfiguration>();

    var endpoint = configuration["Minio:Endpoint"];
    var accessKey = configuration["Minio:AccessKey"];
    var secretKey = configuration["Minio:SecretKey"];

    var client = new MinioClient()
        .WithEndpoint(endpoint)
        .WithCredentials(accessKey, secretKey)
        .Build();

    return client;
});

// Add services to the container.
builder.Services.AddDbContext<MedicalContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddControllers();

// Register Repository
builder.Services.AddScoped<IRepository<Patient>, PatientRepository>();
builder.Services.AddScoped<IRepository<Checkup>, CheckupRepository>();
builder.Services.AddScoped<IRepository<MedicalRecord>, MedicalRecordRepository>();



var app = builder.Build();

app.UseRouting();
//app.UseAuthorization();
app.MapControllers();

app.Run();