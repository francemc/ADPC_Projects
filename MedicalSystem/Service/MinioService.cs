using Minio.DataModel.Args;
using Minio.Exceptions;
using Minio;



public class MinioService
{
    private readonly IMinioClient _minioClient;

    public MinioService(string endpoint, string accessKey, string secretKey)
    {

        _minioClient = new MinioClient()
            .WithEndpoint(endpoint)
            .WithCredentials(accessKey, secretKey)
            .Build();
    }

    public async Task UploadFileAsync(string bucketName, string objectName, Stream fileStream, string contentType)
    {
        try
        {
            // Check if the bucket exists, if not create it
            bool found = await _minioClient.BucketExistsAsync(new BucketExistsArgs().WithBucket(bucketName));
            if (!found)
            {
                await _minioClient.MakeBucketAsync(new MakeBucketArgs().WithBucket(bucketName));
            }

            // Upload the file
            await _minioClient.PutObjectAsync(new PutObjectArgs()
                .WithBucket(bucketName)
                .WithObject(objectName)
                .WithStreamData(fileStream)
                .WithObjectSize(fileStream.Length)
                .WithContentType(contentType));
        }
        catch (MinioException e)
        {
            Console.WriteLine("File Upload Error: {0}", e.Message);
            throw;
        }
    }

    public async Task<Stream> DownloadFileAsync(string bucketName, string objectName)
    {
        try
        {
            var memoryStream = new MemoryStream();
            await _minioClient.GetObjectAsync(new GetObjectArgs()
                .WithBucket(bucketName)
                .WithObject(objectName)
                .WithCallbackStream(stream => stream.CopyTo(memoryStream)));

            memoryStream.Position = 0; // Reset the stream position
            return memoryStream;
        }
        catch (MinioException e)
        {
            Console.WriteLine("File Download Error: {0}", e.Message);
            throw;
        }
    }
}
